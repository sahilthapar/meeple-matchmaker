"""Test file for all message handlers"""

from types import SimpleNamespace
import pytest

from src.constants import MEEPLE_MARKET_CHAT_ID
from src.message_handlers import (
    find_matching_posts,
    get_matching_post_message_contents,
    message_handler,
)
from src.models import Post, Game, User
from tests.helpers import initialize_post


class TestMessageHandlers:
    """Class containing all test cases for message handlers"""

    @pytest.fixture(name="mock_context")
    def mock_context(self, mocker):
        """Fixture to mock a telegram context"""
        mocker.patch("telegram.ext.ContextTypes.DEFAULT_TYPE")

    def test_get_matching_post_message_contents_includes_post_link_for_sale_posts(
        self, database
    ):
        """Sale posts should render a user tag plus a direct link to the post."""
        post = initialize_post(
            post_type="sale",
            text="#sale terraforming mars",
            active=True,
            user_id=101,
            user_name="alpha",
            game_id=167791,
            game_name="Terraforming Mars",
        )
        post.telegram_msg_id = 42
        post.save()

        contents = get_matching_post_message_contents(post)

        assert contents == (
            "[alpha](tg://user?id=101) "
            f"[(Post)](tg://privatepost?channel={str(MEEPLE_MARKET_CHAT_ID)[4:]}&post=42)"
        )

    def test_get_matching_post_message_contents_omits_post_link_for_non_sale_posts(
        self, database
    ):
        """Non-sale posts should only include the user tag."""
        post = initialize_post(
            post_type="search",
            text="#lookingfor terraforming mars",
            active=True,
            user_id=102,
            user_name="beta",
            game_id=167791,
            game_name="Terraforming Mars",
        )

        contents = get_matching_post_message_contents(post)

        assert contents == "[beta](tg://user?id=102)"

    def test_find_matching_posts_renders_matching_active_posts(self, database):
        """Matching posts should be rendered as a comma-separated list."""
        game = Game.get_or_create(game_id=167791, game_name="Terraforming Mars")[0]
        seller = User.get_or_create(telegram_userid=101, first_name="alpha")[0]
        buyer = User.get_or_create(telegram_userid=202, first_name="beta")[0]

        sale_post = Post.create(
            post_type="sale",
            text="#sale terraforming mars",
            active=True,
            user=seller,
            game=game,
            telegram_msg_id=42,
        )
        search_post = Post.create(
            post_type="search",
            text="#lookingfor terraforming mars",
            active=True,
            user=buyer,
            game=game,
        )

        reply = find_matching_posts(search_post)

        assert reply == (
            "[alpha](tg://user?id=101) "
            f"[(Post)](tg://privatepost?channel={str(MEEPLE_MARKET_CHAT_ID)[4:]}&post={sale_post.telegram_msg_id})"
        )

    @pytest.mark.parametrize(
        argnames="init_posts,new_messages,expected_replies,chat_type,expected_reaction, chat_id",
        argvalues=[
            # simple scenario with a two sale posts followed by a search post
            (
                [
                    (
                        "sale",
                        167791,
                        "#seekinginterest terraforming mars",
                        "101",
                        "alpha",
                        1,
                        "Terraforming Mars",
                    ),
                    (
                        "sale",
                        167791,
                        "#sell terraforming mars",
                        "102",
                        "beta",
                        1,
                        "Terraforming Mars",
                    ),
                ],
                [
                    SimpleNamespace(
                        text="#lookingfor terraforming mars",
                        id=9999,
                        first_name="Jacob",
                    )
                ],
                ["[alpha](tg://user?id=101), [beta](tg://user?id=102)"],
                "private",
                "👍",
                123,
            ),
            # simple scenario with a two search posts followed by a sale post
            (
                [
                    (
                        "search",
                        167791,
                        "#lookingfor terraforming mars",
                        "101",
                        "alpha",
                        1,
                        "Terraforming Mars",
                    ),
                    (
                        "search",
                        167791,
                        "#lookingfor terraforming mars",
                        "102",
                        "beta",
                        1,
                        "Terraforming Mars",
                    ),
                ],
                [
                    SimpleNamespace(
                        text="#sell terraforming mars", id=9999, first_name="Jacob"
                    )
                ],
                ["[alpha](tg://user?id=101), [beta](tg://user?id=102)"],
                "group",
                "👍",
                MEEPLE_MARKET_CHAT_ID,
            ),
            # simple scenario with a sale post followed by a sold post
            (
                [
                    (
                        "sale",
                        167791,
                        "#seekinginterest terraforming mars",
                        "101",
                        "alpha",
                        1,
                        "Terraforming Mars",
                    ),
                ],
                [
                    SimpleNamespace(
                        text="#sold terraforming mars", id=101, first_name="Alpha"
                    )
                ],
                [""],
                "private",
                "👍",
                123,
            ),
            # simple scenario with a search post followed by a found post (private chat)
            (
                [
                    (
                        "search",
                        167791,
                        "#lookingfor terraforming mars",
                        "101",
                        "alpha",
                        1,
                        "Terraforming Mars",
                    )
                ],
                [
                    SimpleNamespace(
                        text="#found terraforming mars", id=101, first_name="Alpha"
                    )
                ],
                [""],
                "private",
                "👍",
                123,
            ),
            # simple scenario with a search post followed by a found post (group chat)
            (
                [
                    (
                        "search",
                        167791,
                        "#lookingfor terraforming mars",
                        "101",
                        "alpha",
                        1,
                        "Terraforming Mars",
                    )
                ],
                [
                    SimpleNamespace(
                        text="#found terraforming mars", id=101, first_name="Alpha"
                    )
                ],
                [""],
                "group",
                "👎",
                MEEPLE_MARKET_CHAT_ID,
            ),
            # simple scenario with a sale post in private chat
            (
                [
                    (
                        "search",
                        167791,
                        "#lookingfor terraforming mars",
                        "101",
                        "alpha",
                        1,
                        "Terraforming Mars",
                    )
                ],
                [
                    SimpleNamespace(
                        text="#sell terraforming mars", id=102, first_name="Beta"
                    )
                ],
                [""],
                "private",
                "👎",
                123,
            ),
            # simple scenario with a search post followed by a sell post (in external group chat)
            (
                [
                    (
                        "sell",
                        167791,
                        "#lookingfor terraforming mars",
                        "101",
                        "alpha",
                        1,
                        "Terraforming Mars",
                    )
                ],
                [
                    SimpleNamespace(
                        text="#sell terraforming mars", id=101, first_name="Beta"
                    )
                ],
                [""],
                "group",
                "👎",
                123,
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
            "scenario7-simple-search-followed-by-a-sell-external-group",
        ],
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
        chat_id,
        bgg_client,
    ):
        """Tests multiple scenarios passed to the message handler"""
        for (
            post_type,
            game_id,
            text,
            user_id,
            user_name,
            active,
            game_name,
        ) in init_posts:
            initialize_post(
                post_type=post_type,
                text=text,
                active=active,
                user_id=user_id,
                user_name=user_name,
                game_id=game_id,
                game_name=game_name,
            )

        # call message handler with a new message or multiple new messages
        for msg, reply in zip(new_messages, expected_replies):
            mock_update.message.text = msg.text
            mock_update.message.from_user.id = msg.id
            mock_update.message.from_user.first_name = msg.first_name
            mock_update.effective_chat.type = chat_type
            mock_update.effective_chat.id = chat_id
            await message_handler(mock_update, mock_context, bgg_client)
            if reply:
                mock_update.message.reply_text.assert_called_once_with(
                    reply, parse_mode="Markdown"
                )
            mock_update.message.set_reaction.assert_called_once_with(expected_reaction)
            # Reset so that assert_called_once doesnt trip if more than one message is present
            mock_update.message.reply_text.reset_mock()

        # Additional assertions for 'sold' and 'found' scenarios
        if any(msg.text.lower().startswith("#sold") for msg in new_messages):
            # For 'sold', the user's sale post for the game should be inactive
            for (
                post_type,
                game_id,
                text,
                user_id,
                user_name,
                active,
                game_name,
            ) in init_posts:
                if post_type == "sale":
                    user = User.get(telegram_userid=user_id)
                    game = Game.get(game_id=game_id)
                    post = Post.get(user=user, game=game, post_type=post_type)
                    assert post.active is False
        if any(msg.text.lower().startswith("#found") for msg in new_messages):
            for (
                post_type,
                game_id,
                text,
                user_id,
                user_name,
                active,
                game_name,
            ) in init_posts:
                if post_type == "search":
                    user = User.get(telegram_userid=user_id)
                    game = Game.get(game_id=game_id)
                    post = Post.get(user=user, game=game, post_type=post_type)
                    if chat_type == "private":
                        assert post.active is False
                    else:
                        assert post.active is True
