import pytest
import textwrap
from boardgamegeek import BGGClient

from src.command_handlers import format_list_of_posts, format_post
from src.models import db
from tests.test_message_handlers import TestMessageHandlers
from src.database import init_tables

class TestCommandHandlers:
    @pytest.fixture(name="bgg_client")
    def bgg_client(self):
        return BGGClient()

    @pytest.fixture(name="database")
    def database(self):
        db.init(":memory:")
        return db

    @pytest.mark.parametrize(
        argnames="posts,expected_reply",
        argvalues=[
            (   # post_type, game_id, user_id, user_name, game_name
                [
                    ('sale', 167791, '101', 'Jacob', "Terraforming Mars", 1),
                    ('sale', 167791, '103', 'Vikrant', "Terraforming Mars", 1),
                    ('sale', 342942, '101', 'Jacob', 'Ark Nova', 1),
                ],
                "\nActive sales:"
                "\nTerraforming Mars: [Jacob](tg://user?id=101)"
                "\nTerraforming Mars: [Vikrant](tg://user?id=103)"
                "\nArk Nova: [Jacob](tg://user?id=101)\n"
            ),
            (
                [
                    ('search', 167791, '102', 'Henry', "Terraforming Mars", 1),
                    ('search', 1406, '101', 'Jacob', "Monopoly", 1),
                    ('search', 1406, '102', 'Henry', "Monopoly", 1),
                ],
                "\n\nActive searches:"
                "\nTerraforming Mars: [Henry](tg://user?id=102)"
                "\nMonopoly: [Jacob](tg://user?id=101)"
                "\nMonopoly: [Henry](tg://user?id=102)"
            ),
            (
                [
                    ('sale', 167791, '101', 'Jacob', "Terraforming Mars", 1),
                    ('sale', 167791, '103', 'Vikrant', "Terraforming Mars", 1),
                    ('sale', 342942, '101', 'Jacob', "Ark Nova", 1),
                    ('search', 167791, '102', 'Henry', "Terraforming Mars", 1),
                    ('search', 1406, '101', 'Jacob', 'Monopoly', 1),
                    ('search', 1406, '102', 'Henry', "Monopoly", 1),
                ],
                "\nActive sales:"
                "\nTerraforming Mars: [Jacob](tg://user?id=101)"
                "\nTerraforming Mars: [Vikrant](tg://user?id=103)"
                "\nArk Nova: [Jacob](tg://user?id=101)"
                "\n"
                "\nActive searches:"
                "\nTerraforming Mars: [Henry](tg://user?id=102)"
                "\nMonopoly: [Jacob](tg://user?id=101)"
                "\nMonopoly: [Henry](tg://user?id=102)"
            ),
        ],
        ids=[
            "list_active_sales",
            "list_active_searches",
            "list_all_posts",
        ]

    )
    def test_format_list_of_posts(self, database, posts, expected_reply):
        init_tables(database)
        posts_orm = []
        for post_type, game_id, user_id, user_name, game_name, active in posts:
            posts_orm.append(
                TestMessageHandlers.initialize_post(
                    post_type=post_type, text='', active=active,
                    user_id=user_id, user_name=user_name,
                    game_id=game_id, game_name=game_name
                )
            )
        assert list(format_list_of_posts(posts_orm))[0] == textwrap.dedent(expected_reply)

    @pytest.mark.parametrize(
        argnames="post,expected_response",
        argvalues=[
            (
                # post_type, game_id, user_id, user_name, game_name, active
                ('sale', 167791, '101', 'Jacob', "Terraforming Mars", 1),
                "Terraforming Mars: [Jacob](tg://user?id=101)"
            ),
        ],
        ids=[
            "format_single_post"
        ]

    )
    def test_format_post(self, bgg_client, database, post, expected_response):
        init_tables(database)
        post_type, game_id, user_id, user_name, game_name, active = post
        post = TestMessageHandlers.initialize_post(
                post_type=post_type, text='', active=active,
                user_id=user_id, user_name=user_name,
                game_id=game_id, game_name=game_name
            )
        assert format_post(post, bgg_client) == textwrap.dedent(expected_response)
