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
            (
                [
                    ('sale', 167791, '#seekinginterest terraforming mars', '101', 'Jacob', 1),
                    ('sale', 167791, '#seekinginterest terraforming mars', '103', 'Vikrant', 1),
                    ('sale', 342942, '#selling ark nova', '101', 'Jacob', 1),
                ],
                "\nActive sales:"
                "\nTerraforming Mars: [Jacob](tg://user?id=101)"
                "\nTerraforming Mars: [Vikrant](tg://user?id=103)"
                "\nArk Nova: [Jacob](tg://user?id=101)\n"
            ),
            (
                [
                    ('search', 167791, '#lookingfor terraforming mars', '102', 'Henry', 1),
                    ('search', 1406, '#lookingfor monopoly', '101', 'Jacob', 1),
                    ('search', 1406, '#lookingfor monopoly', '102', 'Henry', 1),
                ],
                "\n\nActive searches:"
                "\nTerraforming Mars: [Henry](tg://user?id=102)"
                "\nMonopoly: [Jacob](tg://user?id=101)"
                "\nMonopoly: [Henry](tg://user?id=102)"
            ),
            (
                [
                    ('sale', 167791, '#seekinginterest terraforming mars', '101', 'Jacob', 1),
                    ('sale', 167791, '#seekinginterest terraforming mars', '103', 'Vikrant', 1),
                    ('sale', 342942, '#selling ark nova', '101', 'Jacob', 1),
                    ('search', 167791, '#lookingfor terraforming mars', '102', 'Henry', 1),
                    ('search', 1406, '#lookingfor monopoly', '101', 'Jacob', 1),
                    ('search', 1406, '#lookingfor monopoly', '102', 'Henry', 1),
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
    def test_format_list_of_posts(self, posts, expected_reply):
        assert format_list_of_posts(posts) == textwrap.dedent(expected_reply)

    @pytest.mark.parametrize(
        argnames="post,expected_response",
        argvalues=[
            (
                ('sale', 167791, '#seekinginterest terraforming mars', '101', 'Jacob', 1),
                "Terraforming Mars: [Jacob](tg://user?id=101)"
            ),
        ],
        ids=[
            "format_single_post"
        ]

    )
    def test_format_post(self, bgg_client, post, expected_response):
        assert format_post(post, bgg_client) == textwrap.dedent(expected_response)

