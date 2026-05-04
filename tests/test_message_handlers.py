"""Test file for all message handlers"""
from types import SimpleNamespace
import pytest

from src.message_handlers import message_handler
from src.models import Post, Game, User
from tests.helpers import initialize_post

class TestMessageHandlers:
    """Class containing all test cases for message handlers"""

    @pytest.fixture(name="mock_context")
    def mock_context(self, mocker):
        """Fixture to mock a telegram context"""
        mocker.patch("telegram.ext.ContextTypes.DEFAULT_TYPE")

    @pytest.mark.parametrize(
        argnames="init_posts,new_messages,expected_replies,chat_type,expected_reaction",
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
                ],
                "private",
                "👍"
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
                ],
                "group",
                "👍"
            ),
            # simple scenario with a sale post followed by a sold post
            (
                [
                    ('sale', 167791, '#seekinginterest terraforming mars', '101', 'alpha', 1, 'Terraforming Mars'),
                ],
                [
                    SimpleNamespace(text="#sold terraforming mars", id=101, first_name="Alpha")
                ],
                [''],
                "private",
                "👍"
            ),
            # simple scenario with a search post followed by a found post (private chat)
            (
                [
                    ('search', 167791, '#lookingfor terraforming mars', '101', 'alpha', 1, 'Terraforming Mars')
                ],
                [
                    SimpleNamespace(text="#found terraforming mars", id=101, first_name="Alpha")
                ],
                [''],
                "private",
                "👍"
            ),
            # simple scenario with a search post followed by a found post (group chat)
            (
                [
                    ('search', 167791, '#lookingfor terraforming mars', '101', 'alpha', 1, 'Terraforming Mars')
                ],
                [
                    SimpleNamespace(text="#found terraforming mars", id=101, first_name="Alpha")
                ],
                [''],
                "group",
                "👎"
            ),
            # simple scenario with a sale post in private chat
            (
                [
                    ('search', 167791, '#lookingfor terraforming mars', '101', 'alpha', 1, 'Terraforming Mars')
                ],
                [
                    SimpleNamespace(text="#sell terraforming mars", id=102, first_name="Beta")
                ],
                [''],
                "private",
                "👎"
            ),
            # todo: scenario with disable notifications in between
        ],
        ids=[
            "scenario1-simple-sales-followed-by-a-search",
            "scenario2-simple-searches-followed-by-a-sale",
            "scenario3-simple-sale-followed-by-a-sold",
            "scenario4-simple-search-followed-by-a-found-private",
            "scenario5-simple-search-followed-by-a-found-group",
            "scenario6-simple-search-followed-by-a-sell-private",
        ]
    )
    async def test_scenario(
        self,
        database,
        init_posts,
        mock_update,
        mock_context,
        new_messages,
        expected_replies,
        chat_type,
        expected_reaction,
        bgg_client):
        """Tests multiple scenarios passed to the message handler"""
        for post_type, game_id, text, user_id, user_name, active, game_name in init_posts:
            initialize_post(
                post_type=post_type, text=text, active=active,
                user_id=user_id, user_name=user_name,
                game_id=game_id, game_name=game_name
            )

        # call message handler with a new message or multiple new messages
        for msg, reply in zip(new_messages, expected_replies):
            mock_update.message.text = msg.text
            mock_update.message.from_user.id = msg.id
            mock_update.message.from_user.first_name = msg.first_name
            mock_update.effective_chat.type = chat_type

            await message_handler(mock_update, mock_context,bgg_client)
            if reply:
                mock_update.message.reply_text.assert_called_once_with(reply, parse_mode="Markdown")
            mock_update.message.set_reaction.assert_called_once_with(expected_reaction)
            # Reset so that assert_called_once doesnt trip if more than one message is present
            mock_update.message.reply_text.reset_mock()

        # Additional assertions for 'sold' and 'found' scenarios
        if any(msg.text.lower().startswith("#sold") for msg in new_messages):
            # For 'sold', the user's sale post for the game should be inactive
            for post_type, game_id, text, user_id, user_name, active, game_name in init_posts:
                if post_type == "sale":
                    user = User.get(telegram_userid=user_id)
                    game = Game.get(game_id=game_id)
                    post = Post.get(user=user, game=game, post_type=post_type)
                    assert post.active is False
        if any(msg.text.lower().startswith("#found") for msg in new_messages):
            for post_type, game_id, text, user_id, user_name, active, game_name in init_posts:
                if post_type == "search":
                    user = User.get(telegram_userid=user_id)
                    game = Game.get(game_id=game_id)
                    post = Post.get(user=user, game=game, post_type=post_type)
                    if chat_type == "private":
                        assert post.active is False
                    else:
                        assert post.active is True
