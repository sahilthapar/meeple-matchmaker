# Testing Review — Meeple Matchmaker

A review of the current test suite and the source code changes that would make the project easier to test. Written as a learning document, so Python classes, Peewee (the ORM), and pytest (the test runner) are explained inline where they matter.

---

## 0. Background primer (skip if familiar)

A few concepts appear repeatedly below. Here is the minimum to follow the review.

- **Class** — a container for related functions ("methods") and data. In this project, `TestDatabase` is a class that groups database-related tests. The `self` parameter you see as the first argument to every method is how the method refers to its own instance. You can think of a test class as a folder.
- **Peewee ORM** — a library that turns Python classes into database tables. `class User(Model)` in `src/models.py` means "there is a SQL table called `user`, and each row becomes a `User` object in Python." `User.get(telegram_userid=101)` runs `SELECT * FROM user WHERE telegram_userid = 101` and gives you back a `User` object.
- **pytest fixture** — a reusable setup function. When a test function has a parameter named `database`, pytest finds a fixture called `database`, runs it, and passes the result in. Fixtures typically live in `conftest.py` so many test files can share them.
- **Parametrize** — `@pytest.mark.parametrize` runs the same test multiple times with different inputs. Each input set becomes a separate test case in the report.
- **Mock** — a stand-in object that pretends to be a real dependency. Used so tests don't hit the real Telegram API or real BoardGameGeek API.
- **Dependency injection (DI)** — instead of a function creating its own dependencies (e.g., `bgg_client = BGGClient(...)` inside the function), it takes them as arguments. DI is the single biggest testability improvement available in this codebase — it comes up repeatedly below.

---

## 1. Issues in the test suite

### 1.1 `tests/conftest.py`

**`database` fixture does not clean up between tests.** The fixture calls `db.init(":memory:")` but never drops tables or closes the connection at the end. Two tests running in the same session can see each other's data. Today tests pass because each test calls `init_tables(database)` and SQLite `CREATE TABLE IF NOT EXISTS` is idempotent — but rows from a previous test linger. The fix is to wrap it as a `yield` fixture with teardown:

```python
@pytest.fixture(name="database")
def database():
    db.init(":memory:")
    db.connect(reuse_if_open=True)
    db.create_tables([User, Game, Post, UserCollection])
    yield db
    db.drop_tables([User, Game, Post, UserCollection])
    db.close()
```

Why this matters: pytest runs tests in file order by default, but parallel runners (`pytest-xdist`) or `--randomly-seed` can re-order. A test suite that depends on order is a bug waiting for a CI config change.

**`initialize_post` is a helper, not a fixture.** It is a plain module-level function imported from `conftest.py` by other files. `conftest.py` is meant for fixtures and pytest hooks — plain helpers belong in a separate file like `tests/helpers.py`. Right now it works because Python imports are forgiving, but it blurs the role of `conftest.py` for a new reader.

**`MockBGGClient` does not match the real client's contract.** The real `BGGClient.game()` raises `BGGItemNotFoundError` when a game is not found. The mock returns `None`. Source code in `src/telegrampost.py:60-85` branches on that exception — so the exception-handling path in `get_game_details` is never actually exercised in tests. Either:
- Make the mock raise `BGGItemNotFoundError` when no match is found, or
- Change `get_game_details` to treat `None` and the exception identically (then document and test both).

**`MockBGGClient.game()` ignores the `exact` parameter.** Real calls pass `exact=True` first and fall back to `exact=False` (fuzzy). The mock uses substring matching for both. Tests cannot detect a bug where production code only calls the fuzzy path or only the exact path.

**`MockBGGClient` is used inconsistently.** In `test_command_handlers.py` the fixture returns the *class* (`return MockBGGClient`), in `test_post.py` it returns an *instance* (`return MockBGGClient()`). A class and an instance are different things — `MockBGGClient.game(...)` called on the class would fail because `self` is missing. It happens to work in `test_command_handlers.py` only because `format_post` short-circuits before calling `bgg_client.game(...)` (the game name is already in the DB). Pick one: always instances.

**Naming: `gameArray` uses camelCase.** Python convention is snake_case (`game_array`). Not a functional bug; just inconsistent with the rest of the codebase and with what a linter would expect.

### 1.2 `tests/test_command_handlers.py`

**Most command handlers are untested.** `src/command_handlers.py` defines nine async handlers. Only the helpers `format_post` and `format_list_of_posts` are tested. Untested: `start_command`, `disable_command`, `list_all_active_sales`, `list_all_active_searches`, `list_my_active_posts`, `add_bgg_username`, `disable_user`, `import_my_bgg_collection`, `match_me`. These are the user-facing entry points and the bugs users will actually file. Missing coverage here is the biggest gap in the suite.

**`bgg_client` fixture returns the class, not an instance.** See the conftest note above.

**`init_tables(database)` is called inside every test.** That line is boilerplate that should live in the fixture. Right now, forgetting it in one test would fail in a confusing way (`Peewee: Table "user" does not exist`).

**Trailing-newline fragility.** Expected replies hard-code exact whitespace including trailing newlines. If `format_list_of_posts` changes its formatting slightly, all tests break at once. For user-visible strings, consider normalizing whitespace in the assertion (`.strip()`) or comparing structured data (list of `(game_name, user_name, user_id)` tuples) rather than the final string.

### 1.3 `tests/test_database.py`

**Stale test data.** The `sample_posts` fixture inserts posts with text like `'#seekinginterest terraforming mars'`. The recent commit `e3e1614 Removed seekinginterest from tag parser` removed that tag. The text field here is no longer meaningful — nobody would produce a post like that anymore. Update the sample data to use a currently-valid tag (`#selling`, `#sell`, etc.).

**`test_init_tables` is vacuously true.** The assertion loops over the tables that exist and checks each is in a whitelist. If `init_tables` created zero tables, the loop runs zero times and the test passes. The right assertion is the other direction — each expected table must be in the list of tables that exist:

```python
for expected in ['game', 'user', 'user_post', 'user_collection']:
    assert expected in tables
```

**Test reaches into the ORM to verify state instead of using the module's API.** `test_disable_posts_all` runs `Post.select().where((~Post.active) & (Post.user == jacob)).execute()` to verify the result. That means the test is coupled to Peewee query syntax. It would be cleaner to call `read_posts(user_id=..., is_active=False)` — the same public function that real callers would use — so the test also exercises `read_posts` with the `is_active=False` branch (currently not tested).

**Error paths are untested.** `disable_posts` calls `User.get(telegram_userid=user_id)` which raises `DoesNotExist` if the user is missing. `read_posts` has the same behavior. Neither the raise nor any graceful handling is covered. Add a test like:

```python
def test_disable_posts_unknown_user_raises(self, database):
    init_tables(database)
    with pytest.raises(User.DoesNotExist):
        disable_posts(user_id=999999)
```

**Result ordering is assumed without a deterministic sort in the test.** The `read_posts` query has `order_by(Post.post_type, Game.game_name, User.first_name)`. The expected lists in `test_read_posts` happen to be in that order, but the relationship is implicit. A single comment (`# results sorted by post_type, game_name, user`) would make this clearer, or sort both sides before comparing.

### 1.4 `tests/test_message_handlers.py`

**Real BGG API calls leak into tests.** `src/message_handlers.py:46` creates `BGGClient(...)` inside the handler. The test's `mock_update` and `mock_context` fixtures do not intercept this, so every test case that reaches `parse_message` calls the real BGG API. This is:
- Slow — dozens of HTTP round-trips per `make test`.
- Flaky — tests fail when BGG is down or rate-limits.
- Environment-dependent — `BGG_BEARER` env var affects behavior.

This is the same root cause as the `MockBGGClient` issue, but here the mock is never wired in at all. **The fix is in `src/`**, not the test — see §2.1.

**Helper is duplicated.** `TestMessageHandlers.initialize_post` is a static method that is identical in shape to `conftest.initialize_post`. Import the one from `conftest` instead of maintaining two copies.

**`assert_called_once_with` inside a loop will fail on the second iteration.** The scenario loop zips `new_messages` with `expected_replies` and asserts `reply_text.assert_called_once_with(...)`. If any scenario is extended to use two messages, the second call will trip the "once" check because the mock has already been called. Use `assert_called_with` (checks last call) or reset the mock between iterations (`mock_update.message.reply_text.reset_mock()`).

**Duplicate test ID.** Two scenarios use `scenario5-...` as the prefix:
- `scenario5-simple-search-followed-by-a-found-group`
- `scenario5-simple-search-followed-by-a-sell-private`

Rename the second to `scenario6-...`. pytest allows duplicate IDs but they confuse reports.

**TODO scenario is still open.** The comment `# todo: scenario with disable notifications in between` is a known gap.

**Reaction assertion bug.** `set_reaction.assert_called_once_with(expected_reaction)` is inside the loop too. Same "called once" bug. For a multi-message scenario it would fire twice and the test would fail.

### 1.5 `tests/test_post.py`

**No module or class docstrings.** `test_command_handlers.py` and `test_database.py` have them; this file does not. Minor, but inconsistent.

**`initialize_db` fixture duplicates the `database` fixture.** It calls `db.init(":memory:")` directly instead of requesting the `database` fixture from `conftest.py`. That means this file's fixture bypasses any future teardown added to the shared fixture. Have it take `database` as a parameter:

```python
@pytest.fixture(name="initialize_db")
def initialize_db(self, database):
    init_tables(database)
```

**`test_is_post_type_banned` only covers four cases.** It misses:
- `search` in private and in group (should be allowed in both)
- `sold` in private and group (allowed in both)
- unknown post_type (returns False, not tested)

**`test_parse_game_name` case `"just a #message no game"` expects the raw string back.** That is odd because `#message` is inside the text, not a parsed tag. The current behavior is "if no recognisable game format exists, return the first line verbatim." That may be right, but a docstring on `parse_game_name` would make this explicit; without one the test reads as a typo.

### 1.6 Cross-cutting issues

**No test coverage configuration.** `pytest-cov` is listed in `requirements.txt` but `pytest.ini` does not enable it. Add:

```ini
[pytest]
testpaths = tests
addopts = --cov=src --cov-report=term-missing --cov-fail-under=70
```

`--cov-fail-under` sets a floor; CI fails if coverage drops. Start low (70%) and raise over time.

**No asyncio mode configured.** `test_message_handlers.py:10` uses the line-level `pytest_plugins = ('pytest_asyncio',)` and each async test needs `@pytest.mark.asyncio`. Simpler: put `asyncio_mode = auto` in `pytest.ini` so every `async def test_...` is recognized automatically.

**No CI config visible.** Recent commits (`Testing gh-actions`, `Fixed test issue`) suggest GitHub Actions is being set up, but no `.github/workflows/` file appears in the listed source — worth confirming it runs `make check` (lint + typecheck + test) on every PR.

**No test factories.** Each test manually constructs `User(telegram_userid=101, first_name='Jacob')`. Consider a small `tests/factories.py` with helpers like `make_user(userid=101)` that default most fields. Third-party libraries like `factory-boy` exist but a handful of functions is enough for this size of project.

**No tests use `pytest.raises`.** There is not a single `with pytest.raises(...)` in the suite. Error paths are an entire category of behavior that is currently uncovered.

**`tests/__init__.py` is empty.** Not wrong, but since `conftest.py` already makes this a pytest package, the `__init__.py` is only needed if you're running with a very old pytest version. Can be removed.

---

## 2. Source changes to make the project more testable

Testing difficulties often point to design problems. The fixes below are also usually *good design* independent of tests.

### 2.1 Inject the BGG client instead of constructing it inside handlers

**Locations:** `src/message_handlers.py:46`, `src/command_handlers.py:44`, `src/command_handlers.py:220`.

**Current pattern** (simplified):

```python
async def message_handler(update, _):
    bgg_client = BGGClient(cache=..., access_token=os.getenv('BGG_BEARER'))
    post, game, user = parse_message(update.message, bgg_client)
```

**Why this hurts tests:** the test gives `message_handler` a mock `update`, but the function reaches out and builds a *real* BGG client that makes real HTTP requests. The test cannot intercept this without monkey-patching the import.

**Fix:** build the BGG client *once*, in `bot.py`, and pass it to handlers via a factory. Two shapes work:

Option A — closure:

```python
# bot.py
def build_message_handler(bgg_client):
    async def handler(update, ctx):
        post, game, user = parse_message(update.message, bgg_client)
        ...
    return handler

bgg_client = BGGClient(...)
app.add_handler(MessageHandler(filters=None, callback=build_message_handler(bgg_client)))
```

Option B — module-level state initialized once by `bot.py` (simpler but makes test setup slightly more manual).

Tests can then pass `MockBGGClient()` into `build_message_handler(...)` with no patching at all. This is the **single highest-value change** for testability.

### 2.2 Split "parse" from "save" in `parse_message` and `create_user_from_message`

**Location:** `src/telegrampost.py:87-145`.

`parse_message` currently does three things: parse, look up the game in BGG, and save everything to the database. Because of the save step, you cannot call `parse_message` in a test without a live DB fixture, and you cannot test the parse logic independently of BGG.

Split into two layers:

1. `parse_message_payload(message) -> ParsedPost` (dataclass / namedtuple, no DB, no network) — pure function, trivially testable.
2. `persist_post(parsed, bgg_client) -> Post` — takes the parsed payload and writes to the DB via BGG.

The current signature returning `(Post, Game, User)` — where all three are already in the DB — is inconvenient for callers too; `message_handler` only cares about `post`, and it has to check all three for `None`.

### 2.3 Make `disable_posts` tolerate missing users

**Location:** `src/database.py:57`.

`User.get(telegram_userid=user_id)` raises `DoesNotExist` for an unknown user. The callers (`/disable`, `#sold`, `#found`) do not catch this, so any unknown user triggers an uncaught exception and a stack trace in logs. Either:

```python
user = User.get_or_none(telegram_userid=user_id)
if user is None:
    return
```

...or document that it raises and have callers handle it. Either choice — but tests should cover the path.

### 2.4 Remove hardcoded admin IDs

**Location:** `src/command_handlers.py:302-306`.

```python
admin_ids = [995823071, 6946013582, 635786234]
```

Put these in `auth.json` or an env var (`MEEPLE_ADMIN_IDS=995823071,6946013582`). Then tests can set a fake admin ID and exercise both the "is admin" and "is not admin" paths of `disable_user` without monkey-patching the module constant.

### 2.5 Make `format_list_of_posts` accept a BGG client

**Location:** `src/command_handlers.py:38-65`.

Same issue as §2.1: this helper builds its own `BGGClient`. It only uses the client for a fallback ("game name missing, look it up") that is probably dead code since `parse_message` always sets the name before saving. Two options:

1. Remove the fallback entirely and drop the BGG dependency.
2. Keep the fallback but accept the client as a parameter.

If (1) is correct, the function becomes a pure string builder and the two existing tests get much simpler.

### 2.6 Replace global logger/env/time dependencies with injected ones (lower priority)

**Locations:** `src/models.py:21,35,55,69` (`datetime.datetime.utcnow`), `src/message_handlers.py:46`, `src/command_handlers.py:44,220` (`os.getenv`).

Calling `datetime.utcnow()` inside a model default means tests cannot produce a stable snapshot of row data (the `updated_at` field changes every run). This has not bitten the current tests because nothing asserts on `updated_at`, but the moment someone does, they will need `freezegun` or a similar helper. Worth noting, not worth fixing today.

### 2.7 Factor `bot.py` startup into a testable function

**Location:** `src/bot.py:19-42`.

Everything runs under `if __name__ == "__main__":`, so there is no way to test "does the bot register all nine handlers?" without invoking polling. Extract:

```python
def build_app(token: str, db_path: str, bgg_client: BGGClient) -> Application:
    app = ApplicationBuilder().token(token).build()
    db.init(db_path)
    init_tables(db)
    # ... register handlers ...
    return app

if __name__ == "__main__":
    ...
    app = build_app(token, "database/meeple-matchmaker.db", BGGClient(...))
    app.run_polling(10)
```

A test can then `build_app(":memory:", MockBGGClient())` and assert on `app.handlers`.

### 2.8 Misc smaller fixes

- **`src/telegrampost.py:12`** uses `getLogger()` (root logger) while every other module uses `getLogger("meeple-matchmaker")`. Make it consistent so tests can capture logs from a single named logger.
- **`src/command_handlers.py:185-193`** `get_status_from_bgg_game` has an implicit `return None` when neither condition matches. Docstring should call this out; tests should cover it (game that is neither for trade, want-to-buy, nor wishlist — today it is silently skipped, which is correct but untested).
- **`src/command_handlers.py:311`** `int(user_to_disable)` with no validation. Pass a non-integer and the admin gets an uncaught `ValueError`. Add a `try/except ValueError` with a user-friendly reply, and test both paths.

---

## 3. Priority ranking

If you only do five things, do these:

1. **Inject the BGG client (§2.1).** Makes `test_message_handlers.py` stop hitting the real API and removes the biggest source of test flakiness.
2. **Fix `MockBGGClient` to match real client behavior (§1.1).** Pick an instance-vs-class shape and match the exception contract.
3. **Clean up the `database` fixture (§1.1).** Add teardown so tests are isolated regardless of order.
4. **Add tests for the untested command handlers (§1.2).** Specifically `disable_user`, `match_me`, `add_bgg_username`, `import_my_bgg_collection`. These are the high-risk user-facing paths.
5. **Enable coverage in `pytest.ini` (§1.6).** Visibility drives the rest of the work.

Everything else in this document is a follow-up, not a blocker.
