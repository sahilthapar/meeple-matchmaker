import pytest
import sqlite3
import textwrap
from boardgamegeek import BGGClient

from src.command_handlers import format_list_of_posts, format_post

class TestCommandHandlers:
    @pytest.fixture(name="con")
    def con(self):
        return sqlite3.connect(":memory:")

    @pytest.fixture(name="cursor")
    def cursor(self, con):
        return con.cursor()

    @pytest.fixture(name="bgg_client")
    def bgg_client(self):
        return BGGClient()

    @pytest.mark.parametrize(
        argnames="posts,expected_reply",
        argvalues=[
            (   # post_type, game_id, user_id, user_name, game_name
                [
                    ('sale', 167791, '101', 'Jacob', "Terraforming Mars"),
                    ('sale', 167791, '103', 'Vikrant', "Terraforming Mars"),
                    ('sale', 342942, '101', 'Jacob', 'Ark Nova'),
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
    def test_format_list_of_posts(self, cursor, posts, expected_reply):
        assert list(format_list_of_posts(cursor, posts))[0] == textwrap.dedent(expected_reply)

    @pytest.mark.parametrize(
        argnames="post,expected_response",
        argvalues=[
            (
                # post_type, game_id, user_id, user_name, game_name
                ('sale', 167791, '101', 'Jacob', "Terraforming Mars"),
                "Terraforming Mars: [Jacob](tg://user?id=101)"
            ),
        ],
        ids=[
            "format_single_post"
        ]

    )
    def test_format_post(self, cursor, bgg_client, post, expected_response):
        assert format_post(cursor, post, bgg_client) == textwrap.dedent(expected_response)

