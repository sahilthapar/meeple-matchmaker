import pytest
from contextlib import nullcontext

from src.telegrampost import TelegramPost, TelegramSearchPost, TelegramSalePost, get_post

class TestPost:
    @pytest.fixture(name="mock_message")
    def mock_message(self, mocker):
        return mocker.patch("telegram.Message")

    @pytest.mark.parametrize(
        argnames="message, expected_type, expected_table_name, expected_game_id",
        argvalues=[
            ("#lOokingFor monopoly", TelegramSearchPost, "search", nullcontext(1406)),
            ("#seekingInterest Terraforming Mars", TelegramSalePost, "sale", nullcontext(167791)),
            ("#sale Guild of Merchant Explorers", TelegramSalePost, "sale", nullcontext(350933)),
            ("#selling Lost Ruins of Arnak", TelegramSalePost, "sale", nullcontext(312484)),
            ("just a #message no game", TelegramPost, "post", pytest.raises(AttributeError))
        ],
        ids=[
            "search", "interest", "sale", "sale-selling", "no-type"
        ]

    )
    def test_get_post(self, mock_message, message, expected_type, expected_table_name, expected_game_id):
        mock_message.text = message
        with expected_game_id as e:
            post = get_post(mock_message)
            assert isinstance(post, expected_type)
            assert post.table_name == expected_table_name
            assert post.game.id == e

    @pytest.mark.parametrize(
        argnames="message, expected_tuple",
        argvalues=[
            ("#lOokingFor monopoly", ("search", 1406, "monopoly", "test", 1)),
            ("#seekingInterest Terraforming Mars", ("sale", 167791, "terraforming mars", "test", 1)),
            ("#sale Guild of Merchant Explorers", ("sale", 350933, "guild of merchant explorers", "test", 1)),
            ("#selling Lost Ruins of Arnak", ("sale", 312484, "lost ruins of arnak", "test", 1))
        ],
        ids=[
            "search", "interest", "sale", "sale-selling"
        ]

    )
    def test_to_db_tuple(self, mock_message, message, expected_tuple):
        mock_message.text = message
        post = get_post(mock_message)
        assert post.insert_into_db is True
        assert post.to_db_tuple() == expected_tuple


