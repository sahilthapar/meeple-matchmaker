import pytest
from boardgamegeek import BGGClient, CacheBackendMemory  #type: ignore
from src.telegrampost import parse_tag, TYPE_LOOKUP, parse_game_name, parse_message, get_game_details, get_message_contents

from src.models import Post, Game, User, db
from src.database import init_tables

class TestMessageParsing:

    @pytest.fixture(name="bgg_client")
    def bgg_client(self):
        return BGGClient(cache=CacheBackendMemory(ttl=3600 * 24 * 7))

    @pytest.fixture(name="mock_message")
    def mock_message(self, mocker):
        return mocker.patch("telegram.Message")

    @pytest.fixture(name="initialize_db")
    def initialize_db(self):
        db.init(":memory:")
        init_tables(db)

    @pytest.mark.parametrize(
        argnames="msg_type, msg_contents",
        argvalues=[
            ("text", "#lookingfor Ark Nova"),
            ("image", "#lookingfor Ark Nova"),
            ("video", "#lookingfor Ark Nova")
        ],
        ids=[
            "text", "image", "video"
        ]
    )
    def test_get_message_contents(self, mock_message, msg_type, msg_contents):
        if msg_type == "text":
            mock_message.text = msg_contents
            mock_message.caption = None
        if msg_type == "image" or msg_type == "video":
            mock_message.text = None
            mock_message.caption = msg_contents

        assert get_message_contents(mock_message) == msg_contents.lower()

    @pytest.mark.parametrize(
        argnames="message, expected",
        argvalues=[
            ("#lookingfor Ark Nova", "#lookingfor"),
            ("#sale Ark Nova", "#sale"),
            ("#selling Ark Nova", "#selling"),
            ("#seekinginterest Ark Nova", "#seekinginterest"),
            ("#sell Ark Nova", "#sell"),
            ("#sold Ark Nova", "#sold"),
            ("#found Ark Nova", "#found"),
            ("#auction Ark Nova", "#auction"),
            ("#iso Ark Nova", "#iso"),
            ("#looking Ark Nova", "#looking"),
        ],
        ids=[
            "search", "sale", "sale-selling", "sale-seekinginterest", "sale-sell",
            "sold", "found", "sale-auction", "search-iso", "search-looking"
        ]
    )
    def test_parse_tag(self, message, expected):
        assert parse_tag(message) == expected

    @pytest.mark.parametrize(
        argnames="tag,expected",
        argvalues=[
            ("#lookingfor", "search"),
            ("#sale", "sale"),
            ("#selling", "sale"),
            ("#seekinginterest", "sale"),
            ("#sell", "sale"),
            ("#sold", "sold"),
            ("#found", "found"),
            ("#iso", "search"),
            ("#looking", "search"),
            ("#auction", "sale"),
        ],
        ids=[
            "lookingfor",
            "sale",
            "selling",
            "seekinginterest",
            "sell",
            "sold",
            "found",
            "iso",
            "looking",
            "auction",
        ]
    )
    def test_type_lookup(self, tag, expected):
        assert TYPE_LOOKUP[tag] == expected

    @pytest.mark.parametrize(
        argnames="message, expected",
        argvalues=[
            ("monopoly", "monopoly"),
            ("just a #message no game", "just a #message no game"),
            (
                """
                monopoly
                """,
                "monopoly"
            ),
            (
                """
                monopoly
                
                condition: good
                """,
                "monopoly"
            ),
            (
                """
                monopoly
                condition: good
                
                location: Delhi/NCR
                """,
                "monopoly"
            ),
            (
                """
                game: kanban ev
                """,
                "kanban ev"
            ),
            (
                """
                game name: kanban ev
                """,
                "kanban ev"
            )
        ],
        ids=[
            "single-line",
            "single-line-no-game",
            "multiline-with-just-game",
            "mutliline-with-condition",
            "multiline-with-more-details-and-links",
            "multiline-with-keyword-game",
            "mutliline-with-keyword-game-name"
            ""
        ]

    )
    def test_parse_game_name(self, message, expected):
        assert parse_game_name(message) == expected

    @pytest.mark.parametrize(
        argnames="game_name, expected_game_id, expected_game_name",
        argvalues=[
            ("monopoly", 1406, "Monopoly"),
            ("terraforming mars", 167791, "Terraforming Mars"),
            ("guild of merchant explorers", 350933, "The Guild of Merchant Explorers"),
            ("lost ruins of arnak", 312484, "Lost Ruins of Arnak"),
            ("just a #message no game", None, None)
        ],
        ids=[
            "monopoly", "TfM", "Guild of Merchant Explorers", "Arnak", "not-a-valid-game"
        ]

    )
    def test_get_game(self, bgg_client, initialize_db, game_name, expected_game_id, expected_game_name):
        game = get_game_details(game_name, bgg_client)
        if not expected_game_id:
            assert game is None
        else:
            assert game.game_id == expected_game_id
            assert game.game_name == expected_game_name

    @pytest.mark.parametrize(
        argnames="message, user_id, expected_type, expected_game_id, expected_game_name",
        argvalues=[
            ("#lOokingFor monopoly", 101, "search", 1406, "Monopoly"),
            ("#seekingInterest Terraforming Mars", 102, "sale", 167791, "Terraforming Mars"),
            ("#sale Guild of Merchant Explorers", 103, "sale", 350933, "The Guild of Merchant Explorers"),
            ("#selling Lost Ruins of Arnak", 104, "sale", 312484, "Lost Ruins of Arnak"),
            ("just a #message no game", 105, "post", None, None)
        ],
        ids=[
            "search", "interest", "sale", "sale-selling", "no-type"
        ]

    )
    def test_parse_message(self, mock_message, initialize_db, message, user_id, expected_type, expected_game_id, expected_game_name):
        mock_message.text = message
        mock_message.from_user.id = user_id
        mock_message.from_user.first_name = str(user_id * 100)
        mock_message.from_user.last_name = str(user_id * 50)

        post, game, user = parse_message(mock_message)

        if not post:
            assert post == expected_game_id
            return

        # check post
        assert isinstance(post, Post)
        assert post.post_type == expected_type
        assert post.game.game_id == expected_game_id
        assert post.user.telegram_userid == user_id
        assert post.user.first_name == str(user_id * 100)
        assert post.game.game_name == expected_game_name
        assert post.active == 1

        # check game
        assert isinstance(game, Game)
        assert game.game_id == expected_game_id
        assert game.game_name == expected_game_name

        # check user
        assert isinstance(user, User)
        assert user.telegram_userid == user_id
        assert user.first_name == str(user_id * 100)
        assert user.last_name == str(user_id * 50)
