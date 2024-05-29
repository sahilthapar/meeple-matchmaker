import pytest
from src.post import Post, SearchPost, InterestPost, SalePost, get_post
from src.game import Game
from src.user import User

class TestPost:
    @pytest.mark.parametrize(
        argnames="message, expected_type",
        argvalues=[
            ("#lOokingFor", SearchPost),
            ("#seekingInterest", InterestPost),
            ("#sale", SalePost),
            ("#selling something", SalePost),
            ("just a #message", Post)
        ],
        ids=[
            "search", "interest", "sale", "sale-selling", "no-type"
        ]

    )
    def test_get_post(self, message, expected_type):
        post = get_post(message)

        assert type(post) == expected_type