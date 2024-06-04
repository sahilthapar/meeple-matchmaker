import pytest
from contextlib import nullcontext
from boardgamegeek.exceptions import BGGItemNotFoundError

from src.post import Post, SearchPost, SalePost, get_post

class TestPost:
    @pytest.mark.parametrize(
        argnames="message, expected_type, expected_table_name, expected_game_id",
        argvalues=[
            ("#lOokingFor monopoly", SearchPost, "search", nullcontext(1406)),
            ("#seekingInterest Terraforming Mars", SalePost, "sale", nullcontext(167791)),
            ("#sale Guild of Merchant Explorers", SalePost, "sale", nullcontext(350933)),
            ("#selling Lost Ruins of Arnak", SalePost, "sale", nullcontext(312484)),
            ("just a #message no game", Post, "post", pytest.raises(AttributeError))
        ],
        ids=[
            "search", "interest", "sale", "sale-selling", "no-type"
        ]

    )
    def test_get_post(self, message, expected_type, expected_table_name, expected_game_id):

        with expected_game_id as e:
            post = get_post(message)
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
    def test_to_db_tuple(self, message, expected_tuple):

        post = get_post(message)
        assert post.insert_into_db is True
        assert post.to_db_tuple() == expected_tuple


