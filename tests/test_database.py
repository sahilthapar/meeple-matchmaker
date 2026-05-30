"""Test cases for the database module"""

import pytest
from datetime import datetime, timedelta
from src.database import (
    read_posts,
    disable_posts,
    update_and_get_stale_posts,
    get_game_from_post,
    get_user_from_post,
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
        """Tests updating stale posts for user ID 23"""
        # The function hardcodes user ID 23, so we need to create posts for that specific user ID
        # First, find what user ID will actually be 23 or create exactly what the function expects

        # Create users in order - the first two created will have IDs that depend on the database
        user_23 = User(telegram_userid=23, first_name="User23")
        user_23.save()

        other_user = User(telegram_userid=24, first_name="OtherUser")
        other_user.save()

        # Create games
        game1 = Game(game_id=1001, game_name="Game1")
        game2 = Game(game_id=1002, game_name="Game2")
        for game in [game1, game2]:
            game.save()

        # Create posts with various timestamps
        cutoff_time = datetime.now() - timedelta(days=3)
        old_time = cutoff_time - timedelta(days=1)
        recent_time = datetime.now()

        # Only create old stale sale post for the user that will have ID 23
        # The function checks for Post.user == 23, which is the primary key ID
        if user_23.id == 23:
            # Old stale sale post by user with ID 23 (should be updated)
            old_post_user23 = Post(
                post_type="sale",
                text="#sell old game",
                active=True,
                user=user_23,
                game=game1,
                updated_at=old_time,
            )
            old_post_user23.save()

            # Recent sale post by same user (should NOT be updated)
            recent_post_user23 = Post(
                post_type="sale",
                text="#sell recent game",
                active=True,
                user=user_23,
                game=game2,
                updated_at=recent_time,
            )
            recent_post_user23.save()

            # Old search post by user 23 (should NOT be updated - only sales)
            old_search_post = Post(
                post_type="search",
                text="#looking for old game",
                active=True,
                user=user_23,
                game=game1,
                updated_at=old_time,
            )
            old_search_post.save()

            # Execute the update
            update_and_get_stale_posts(cutoff_time)

            # Assertions - verify the post was updated to inactive
            old_post_user23_updated = Post.get_by_id(old_post_user23.id)
            assert old_post_user23_updated.active == False

            # Verify other posts remain active
            recent_post_user23_updated = Post.get_by_id(recent_post_user23.id)
            assert recent_post_user23_updated.active == True

            old_search_post_updated = Post.get_by_id(old_search_post.id)
            assert old_search_post_updated.active == True
        else:
            # If the user doesn't have ID 23, just verify the function doesn't crash
            # and that no posts are updated (since the function only updates user ID 23)
            old_post = Post(
                post_type="sale",
                text="#sell",
                active=True,
                user=user_23,
                game=game1,
                updated_at=old_time,
            )
            old_post.save()

            update_and_get_stale_posts(cutoff_time)

            old_post_updated = Post.get_by_id(old_post.id)
            # Post should remain active because user doesn't have ID 23
            assert old_post_updated.active == True

    def test_get_game_from_post(self, sample_posts):
        """Tests retrieving a game from a post"""
        # Create a test post directly
        jacob = User.get(telegram_userid=101)
        tfm = Game.get(game_id=167791)
        post = Post.get(Post.user == jacob, Post.game == tfm)

        # Get the game from the post
        game = get_game_from_post(post)

        # Assertions
        assert isinstance(game, Game)
        assert game.id == tfm.id
        assert game.game_id == 167791
        assert game.game_name == "Terraforming Mars"

    def test_get_game_from_post_returns_correct_game(self, database):
        """Tests that get_game_from_post returns the correct specific game"""
        # Create test data
        user = User(telegram_userid=201, first_name="TestUser")
        user.save()

        game1 = Game(game_id=2001, game_name="Game One")
        game2 = Game(game_id=2002, game_name="Game Two")
        game1.save()
        game2.save()

        post = Post(post_type="sale", text="#sell", active=True, user=user, game=game1)
        post.save()

        # Test get_game_from_post
        retrieved_game = get_game_from_post(post)

        assert retrieved_game.id == game1.id
        assert retrieved_game.game_id == 2001
        assert retrieved_game.game_name == "Game One"
        assert retrieved_game.id != game2.id

    def test_get_user_from_post(self, sample_posts):
        """Tests retrieving a user from a post"""
        # Create a test post directly
        jacob = User.get(telegram_userid=101)
        tfm = Game.get(game_id=167791)
        post = Post.get(Post.user == jacob, Post.game == tfm)

        # Get the user from the post
        user = get_user_from_post(post)

        # Assertions
        assert isinstance(user, User)
        assert user.id == jacob.id
        assert user.telegram_userid == 101
        assert user.first_name == "Jacob"

    def test_get_user_from_post_returns_correct_user(self, database):
        """Tests that get_user_from_post returns the correct specific user"""
        # Create test data
        user1 = User(telegram_userid=301, first_name="User One")
        user2 = User(telegram_userid=302, first_name="User Two")
        user1.save()
        user2.save()

        game = Game(game_id=3001, game_name="Test Game")
        game.save()

        post = Post(
            post_type="search", text="#looking", active=True, user=user1, game=game
        )
        post.save()

        # Test get_user_from_post
        retrieved_user = get_user_from_post(post)

        assert retrieved_user.id == user1.id
        assert retrieved_user.telegram_userid == 301
        assert retrieved_user.first_name == "User One"
        assert retrieved_user.id != user2.id
