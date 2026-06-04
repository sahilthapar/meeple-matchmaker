"""Test cases for the database module"""

import pytest
from datetime import datetime, timedelta
from src.database import (
    read_posts,
    disable_posts,
    update_and_get_stale_posts,
)
from src.models import User, Game, Post


class TestDatabase:
    """Class containing all test cases to be executed for the database"""

    @staticmethod
    def _post_model_to_tuple(post: Post):
        return (
            post.post_type,
            post.game.game_id,
            post.user.first_name,
            post.active,
            post.game.game_name,
        )

    @pytest.fixture(name="sample_posts")
    def sample_posts(self, database):
        """Fixture to initialise the database with a number of users and posts"""
        jacob = User(telegram_userid=101, first_name="Jacob")
        henry = User(telegram_userid=102, first_name="Henry")
        marcus = User(telegram_userid=103, first_name="Marcus")
        cristiano = User(telegram_userid=107, first_name="Cristiano")
        for user in [jacob, henry, marcus, cristiano]:
            user.save()

        tfm = Game(game_id=167791, game_name="Terraforming Mars")
        ark_nova = Game(game_id=321, game_name="Ark Nova")
        destinies = Game(game_id=999, game_name="Destinies")
        monopoly = Game(game_id=123, game_name="Monopoly")
        wingspan = Game(game_id=345, game_name="Wingspan")

        for game in [tfm, ark_nova, destinies, monopoly, wingspan]:
            game.save()

        Post(
            post_type="sale",
            text="#sell terraforming mars",
            active=True,
            user=jacob,
            game=tfm,
        ).save()
        Post(
            post_type="search",
            text="#lookingfor terraforming mars",
            active=True,
            user=henry,
            game=tfm,
        ).save()
        Post(
            post_type="sale",
            text="#selling ark nova",
            active=True,
            user=jacob,
            game=ark_nova,
        ).save()
        Post(
            post_type="sale",
            text="#selling destinies",
            active=False,
            user=marcus,
            game=destinies,
        ).save()
        Post(
            post_type="search",
            text="#lookingfor monopoly",
            active=True,
            user=jacob,
            game=monopoly,
        ).save()
        Post(
            post_type="search",
            text="#lookingfor wingspan",
            active=False,
            user=cristiano,
            game=wingspan,
        ).save()

    def test_init_tables(self, database):
        """Initialises the tables for the in memory fixture database present in conftest"""
        tables = database.get_tables()

        for table in ["game", "user", "user_post", "user_collection"]:
            assert table in tables

    @pytest.mark.parametrize(
        argnames="post_type,game_id,expected_inactives",
        argvalues=[
            # disable_all
            (
                None,
                None,
                [
                    ("sale", 167791, "Jacob", False, "Terraforming Mars"),
                    ("sale", 321, "Jacob", False, "Ark Nova"),
                    ("search", 123, "Jacob", False, "Monopoly"),
                ],
            ),
            # disable terraforming sale for Jacob
            (
                "sale",
                167791,
                [
                    ("sale", 167791, "Jacob", False, "Terraforming Mars"),
                ],
            ),
            # disable monopoly search for Jacob
            ("search", 123, [("search", 123, "Jacob", False, "Monopoly")]),
        ],
        ids=["disable_all", "disable_sold_tfm", "disable_found_monopoly"],
    )
    def test_disable_posts_all(
        self, sample_posts, post_type, game_id, expected_inactives
    ):
        """Tests disabling of posts. sample_posts is a parameter so that the fixture executes"""
        jacob = User.get(telegram_userid=101)

        disable_posts(
            user_id=jacob.telegram_userid, post_type=post_type, game_id=game_id
        )

        # ruff: noqa: E712
        jacobs_inactive_posts = read_posts(
            user_id=jacob.telegram_userid, is_active=False
        )
        actual_inactives = [
            self._post_model_to_tuple(post) for post in jacobs_inactive_posts
        ]
        assert set(actual_inactives) == set(expected_inactives)

    @pytest.mark.parametrize(
        argnames="user_id, post_type, game_id, expected_data",
        argvalues=[
            (
                None,
                "search",
                167791,
                [
                    ("search", 167791, "Henry", True, "Terraforming Mars"),
                ],
            ),
            (
                None,
                "sale",
                167791,
                [
                    ("sale", 167791, "Jacob", True, "Terraforming Mars"),
                ],
            ),
            (
                None,
                "sale",
                None,
                [
                    ("sale", 321, "Jacob", True, "Ark Nova"),
                    ("sale", 167791, "Jacob", True, "Terraforming Mars"),
                ],
            ),
            (
                None,
                "search",
                None,
                [
                    ("search", 123, "Jacob", True, "Monopoly"),
                    ("search", 167791, "Henry", True, "Terraforming Mars"),
                ],
            ),
            (
                101,
                None,
                None,
                [
                    ("sale", 321, "Jacob", True, "Ark Nova"),
                    ("sale", 167791, "Jacob", True, "Terraforming Mars"),
                    ("search", 123, "Jacob", True, "Monopoly"),
                ],
            ),
        ],
        ids=[
            "search_tfm",
            "sale_tfm",
            "list_all_active_sales",
            "list_all_active_searches",
            "list_all_active_posts_for_user",
        ],
    )
    def test_read_posts(self, sample_posts, user_id, post_type, game_id, expected_data):
        """Tests reading of posts. sample_posts is a parameter so that the fixture executes"""
        posts = read_posts(post_type=post_type, user_id=user_id, game_id=game_id)
        # results sorted by post_type, game_name, user
        posts = [self._post_model_to_tuple(post) for post in posts]
        assert posts == expected_data

    def test_update_and_get_stale_posts(self, database):
        """Tests updating stale posts to mark them as inactive based on age"""
        # Create users
        user1 = User(telegram_userid=201, first_name="User1")
        user2 = User(telegram_userid=202, first_name="User2")
        user1.save()
        user2.save()

        # Create games
        game1 = Game(game_id=1001, game_name="Game1")
        game2 = Game(game_id=1002, game_name="Game2")
        for game in [game1, game2]:
            game.save()

        # Create posts with various timestamps
        cutoff_time = datetime.now() - timedelta(days=3)
        old_time = cutoff_time - timedelta(days=1)
        recent_time = datetime.now()

        # Old stale sale post (should be updated to inactive)
        old_stale_sale = Post(
            post_type="sale",
            text="#sell old game",
            active=True,
            user=user1,
            game=game1,
            updated_at=old_time,
        )
        old_stale_sale.save()

        # Recent sale post (should remain active)
        recent_sale = Post(
            post_type="sale",
            text="#sell recent game",
            active=True,
            user=user1,
            game=game2,
            updated_at=recent_time,
        )
        recent_sale.save()

        # Old search post (should remain active - only sales are marked stale)
        old_search = Post(
            post_type="search",
            text="#looking for old game",
            active=True,
            user=user2,
            game=game1,
            updated_at=old_time,
        )
        old_search.save()

        # Old inactive sale post (should remain inactive)
        old_inactive_sale = Post(
            post_type="sale",
            text="#sell old inactive",
            active=False,
            user=user2,
            game=game2,
            updated_at=old_time,
        )
        old_inactive_sale.save()

        # Execute the update
        update_and_get_stale_posts(cutoff_time)

        # Assertions
        old_stale_sale_updated = Post.get_by_id(old_stale_sale.id)
        assert old_stale_sale_updated.active == False

        recent_sale_updated = Post.get_by_id(recent_sale.id)
        assert recent_sale_updated.active == True

        old_search_updated = Post.get_by_id(old_search.id)
        assert old_search_updated.active == True

        old_inactive_sale_updated = Post.get_by_id(old_inactive_sale.id)
        assert old_inactive_sale_updated.active == False
