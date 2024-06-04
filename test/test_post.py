import pytest
from contextlib import nullcontext

from src.telegrampost import TelegramPost, TelegramSearchPost, TelegramSalePost, get_post

class TestPost:
    @pytest.fixture(name="mock_message")
    def mock_message(self, mocker):
        return mocker.patch("telegram.Message")

    @pytest.mark.parametrize(
        argnames="message, user_id, expected_type, expected_table_name, expected_game_id",
        argvalues=[
            ("#lOokingFor monopoly", 101, TelegramSearchPost, "search", 1406),
            ("#seekingInterest Terraforming Mars", 102, TelegramSalePost, "sale", 167791),
            ("#sale Guild of Merchant Explorers", 103, TelegramSalePost, "sale", 350933),
            ("#selling Lost Ruins of Arnak", 104, TelegramSalePost, "sale", 312484),
            ("just a #message no game", 105, TelegramPost, "post", None)
        ],
        ids=[
            "search", "interest", "sale", "sale-selling", "no-type"
        ]

    )
    def test_get_post(self, mock_message, message, user_id, expected_type, expected_table_name, expected_game_id):
        mock_message.text = message
        mock_message.from_user.id = user_id

        post = get_post(mock_message)
        assert isinstance(post, expected_type)
        assert post.table_name == expected_table_name
        assert post.game_id == expected_game_id
        assert post.user_id == user_id

    @pytest.mark.parametrize(
        argnames="message, expected_tuple",
        argvalues=[
            ("#lOokingFor monopoly", ("search", 1406, "monopoly", 101, 1)),
            ("#seekingInterest Terraforming Mars", ("sale", 167791, "terraforming mars", 101, 1)),
            ("#sale Guild of Merchant Explorers", ("sale", 350933, "guild of merchant explorers", 101, 1)),
            ("#selling Lost Ruins of Arnak", ("sale", 312484, "lost ruins of arnak", 101, 1))
        ],
        ids=[
            "search", "interest", "sale", "sale-selling"
        ]

    )
    def test_to_db_tuple(self, mock_message, message, expected_tuple):
        mock_message.text = message
        mock_message.from_user.id = 101
        post = get_post(mock_message)
        assert post.insert_into_db is True
        assert post.to_db_tuple() == expected_tuple


