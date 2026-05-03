# Meeple Matchmaker

A Telegram bot for a board game marketplace group. It parses buy/sell posts, looks up games on BoardGameGeek (BGG), and notifies users when a buyer and seller are interested in the same game.

## Stack

- **Python 3.11**, async via `python-telegram-bot 21.6`
- **SQLite** with **Peewee ORM** (`src/models.py`)
- **BGG API** via `bgg-api` (`src/bgg.py`)
- **Docker / Docker Compose** for deployment

## Commands

```bash
make install    # pip install -r requirements.txt
make test       # pytest
make lint       # ruff check
make start_bot  # python ./src/bot.py
```

## Source Layout

| File | Responsibility |
|------|---------------|
| `src/bot.py` | Entry point — loads token from `auth.json`, wires up handlers, starts polling |
| `src/models.py` | Peewee ORM models: `User`, `Game`, `Post`, `UserCollection` |
| `src/database.py` | DB helpers: `init_tables()`, `read_posts()`, `disable_posts()` |
| `src/telegrampost.py` | Message parsing: hashtag extraction, BGG game lookup, post creation |
| `src/message_handlers.py` | Routes incoming messages — finds matches, disables posts on #sold/#found |
| `src/command_handlers.py` | Slash command handlers (`/list_all_sales`, `/match_me`, `/import_my_bgg_collection`, etc.) |
| `src/bgg.py` | BGG client factory with auth token support and 7-day cache |

## Config

- `auth.json` — Telegram bot token (see `auth.example.json`)
- `.env` — `BGG_BEARER` token for BGG API (avoids rate limits)
- `database/meeple-matchmaker.db` — SQLite database

## Testing

Tests live in `tests/`. An in-memory SQLite database is used via the `database` fixture in `conftest.py` — no real DB or network calls needed.

```bash
pytest                  # all tests
pytest tests/test_post.py   # single file
pytest --cov=src        # with coverage
```

Test files mirror source modules: `test_post.py` → `telegrampost.py`, `test_database.py` → `database.py`, etc.

## Key Concepts

- **Post types:** `search` (#lookingfor, #iso, #looking), `sale` (#sale, #selling, #sell, #auction), `found`, `sold`
- **Matching:** a `search` post matches against active `sale` posts for the same game, and vice versa
- **Deactivation:** `#found` disables the user's active `search` posts; `#sold` disables active `sale` posts
- **BGG lookup:** first tries exact match, falls back to fuzzy match; results are cached for 7 days
- **Admin:** hardcoded admin Telegram user ID in `command_handlers.py` (`/disable_user` command)

## Deployment

```bash
docker compose up -d
```

The bot runs as a non-root `appuser`. Persistent data is stored in the `sqlite-data` Docker volume. Logs use JSON format with 100 MB rotation (5 files).