import asyncio
import pytest
from types import SimpleNamespace

from src.database import init_tables
from src.message_handlers import message_handler

from src.models import Post, Game, User, db
pytest_plugins = ('pytest_asyncio',)

class TestMessageHandlers:

    @pytest.fixture(name="database")
    def database(self):
        db.init(":memory:")
        return db

    @pytest.fixture(name="mock_update")
    def mock_update(self, mocker):
        update = mocker.patch("telegram.Update")
        f = asyncio.Future()
        f.set_result('text')
        update.message.reply_text.return_value = f
        update.message.set_reaction.return_value = f

        return update

    @pytest.fixture(name="mock_context")
    def mock_context(self, mocker):
        mocker.patch("telegram.ext.ContextTypes.DEFAULT_TYPE")

    @staticmethod
    def initialize_post(
            post_type: str, text: str, active: bool,
            user_id: int, user_name: str,
            game_id: int, game_name: str
    ):
        user, _ = User.get_or_create(telegram_userid=user_id, first_name=user_name)
        game, _ = Game.get_or_create(game_id=game_id, game_name=game_name)

        user.save()
        game.save()
        post = Post(post_type=post_type, text=text, active=active, user=user, game=game)
        post.save()

    @pytest.mark.parametrize(
        argnames="init_posts,new_messages,expected_replies",
        argvalues=[
            # simple scenario with a two sale posts followed by a search post
            (
                [
                    ('sale', 167791, '#seekinginterest terraforming mars', '101', 'alpha', 1, 'Terraforming Mars'),
                    ('sale', 167791, '#sell terraforming mars', '102', 'beta', 1, 'Terraforming Mars'),
                ],
                [
                    SimpleNamespace(text="#lookingfor terraforming mars", id=9999, first_name="Jacob")
                ],
                [
                    "[alpha](tg://user?id=101), [beta](tg://user?id=102)"
                ]
            ),
            # simple scenario with a two search posts followed by a sale post
            (
                [
                    ('search', 167791, '#lookingfor terraforming mars', '101', 'alpha', 1, 'Terraforming Mars'),
                    ('search', 167791, '#lookingfor terraforming mars', '102', 'beta', 1, 'Terraforming Mars'),
                ],
                [
                    SimpleNamespace(text="#sell terraforming mars", id=9999, first_name="Jacob")
                ],
                [
                    "[alpha](tg://user?id=101), [beta](tg://user?id=102)"
                ]
            ),
            # simple scenario with a sale post followed by a sold post
            (
                    [
                        ('sale', 167791, '#seekinginterest terraforming mars', '101', 'alpha', 1, 'Terraforming Mars'),
                    ],
                    [
                        SimpleNamespace(text="#sold terraforming mars", id=101, first_name="Alpha")
                    ],
                    ['']
            ),
            # simple scenario with a search post followed by a found post
            (
                    [
                        ('search', 167791, '#lookingfor terraforming mars', '101', 'alpha', 1, 'Terraforming Mars')
                    ],
                    [
                        SimpleNamespace(text="#found terraforming mars", id=101, first_name="Alpha")
                    ],
                    ['']
            ),
            # todo: scenario with disable notifications in between
        ],
        ids=[
            "scenario1-simple-sales-followed-by-a-search",
            "scenario2-simple-searches-followed-by-a-sale",
            "scenario3-simple-sale-followed-by-a-sold",
            "scenario4-simple-search-followed-by-a-found",

        ]
    )
    @pytest.mark.asyncio
    async def test_scenario(self, database, init_posts, mock_update, mock_context, new_messages, expected_replies):
        init_tables(database)
        for post_type, game_id, text, user_id, user_name, active, game_name in init_posts:
            self.initialize_post(
                post_type=post_type, text=text, active=active,
                user_id=user_id, user_name=user_name,
                game_id=game_id, game_name=game_name
            )

        # call message handler with a new message or multiple new messages
        for msg, reply in zip(new_messages, expected_replies):
            mock_update.message.text = msg.text
            mock_update.message.from_user.id = msg.id
            mock_update.message.from_user.first_name = msg.first_name

            await message_handler(mock_update, mock_context)
            # todo: for sold and found scenarios perhaps also assert that the right db methods are being called?
            if reply:
                mock_update.message.reply_text.assert_called_once_with(reply, parse_mode="Markdown")
            mock_update.message.set_reaction.assert_called_once_with("👍")
