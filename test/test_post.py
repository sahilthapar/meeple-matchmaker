import pytest
from src.post import Post, SearchPost, InterestPost, SalePost, get_post
from src.game import Game
from src.user import User

class TestPost:
    @pytest.mark.parametrize(
        argnames="message, expected_type, expected_table_name",
        argvalues=[
            ("#lOokingFor", SearchPost, "search"),
            ("#seekingInterest", InterestPost, "interest"),
            ("#sale", SalePost, "sale"),
            ("#selling something", SalePost, "sale"),
            ("just a #message", Post, "post")
        ],
        ids=[
            "search", "interest", "sale", "sale-selling", "no-type"
        ]

    )
    def test_get_post(self, message, expected_type, expected_table_name):
        post = get_post(message)

        assert type(post) == expected_type
        assert post.table_name == expected_table_name

