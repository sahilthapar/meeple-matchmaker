import pytest
from contextlib import nullcontext
from boardgamegeek import BGGClient
from boardgamegeek.exceptions import BGGItemNotFoundError

from src.post import Post, SearchPost, InterestPost, SalePost, get_post

class TestPost:

    @pytest.fixture(name="bgg_client")
    def bgg_client(self):
        return BGGClient()

    # @pytest.mark.parametrize(
    #     argnames="message, expected_bgg_id",
    #     argvalues=[
    #         ("#lookingfor Monopoly", 1),
    #         ("#selling Ark Nova", 2)
    #     ],
    #     ids=["with_link", "without_link"]
    # )
    # def test_get_game(self, bgg_client, message, expected_bgg_id):
    #
    #     post = Post(message, bgg_client)
    #     assert expected_bgg_id == post.game.id

    @pytest.mark.parametrize(
        argnames="message, expected_type, expected_table_name, expected_game_id",
        argvalues=[
            ("#lOokingFor monopoly", SearchPost, "search", nullcontext(1406)),
            ("#seekingInterest Terraforming Mars", InterestPost, "interest", nullcontext(167791)),
            ("#sale Guild of Merchant Explorers", SalePost, "sale", nullcontext(350933)),
            ("#selling Lost Ruins of Arnak", SalePost, "sale", nullcontext(312484)),
            ("just a #message no game", Post, "post", pytest.raises(BGGItemNotFoundError))
        ],
        ids=[
            "search", "interest", "sale", "sale-selling", "no-type"
        ]

    )
    def test_get_post(self, bgg_client, message, expected_type, expected_table_name, expected_game_id):

        with expected_game_id as e:
            post = get_post(message, bgg_client)
            assert type(post) == expected_type
            assert post.bgg_client == bgg_client
            assert post.table_name == expected_table_name
            assert post.game.id == e


