"""Test cases for the job_queues module"""

import pytest
import datetime
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

from src.job_queues import (
    cleanup_expired_posts,
    inform_user,
    generate_daily_summary,
    generate_weekly_summary,
)
from src.models import User, Game, Post
from src.constants import SALE_EXPIRY_DAYS
from src.messages import generate_stale_post_message


class TestJobQueues:
    """Class containing all test cases for job_queues module"""

    @pytest.fixture(name="mock_context")
    def mock_context(self, mocker):
        """Fixture to mock a telegram context with bot"""
        context = MagicMock()
        context.bot = MagicMock()
        context.bot.send_message = AsyncMock()
        return context

    @pytest.fixture(name="sample_stale_posts")
    def sample_stale_posts(self, database):
        """Fixture to initialize the database with users, games, and stale sale posts"""
        # Create users
        jacob = User(telegram_userid=101, first_name="Jacob")
        henry = User(telegram_userid=102, first_name="Henry")
        marcus = User(telegram_userid=103, first_name="Marcus")
        for user in [jacob, henry, marcus]:
            user.save()

        # Create games
        tfm = Game(game_id=167791, game_name="Terraforming Mars")
        ark_nova = Game(game_id=321, game_name="Ark Nova")
        monopoly = Game(game_id=123, game_name="Monopoly")
        for game in [tfm, ark_nova, monopoly]:
            game.save()

        # Create stale sale posts (older than SALE_EXPIRY_DAYS)
        old_date = datetime.datetime.now(datetime.timezone.utc) - timedelta(
            days=SALE_EXPIRY_DAYS + 10
        )
        recent_date = datetime.datetime.now(datetime.timezone.utc) - timedelta(
            days=SALE_EXPIRY_DAYS - 10
        )

        stale_post_1 = Post(
            post_type="sale",
            text="#sell terraforming mars",
            active=True,
            user=jacob,
            game=tfm,
            created_at=old_date,
        )
        stale_post_1.save()

        stale_post_2 = Post(
            post_type="sale",
            text="#sell ark nova",
            active=True,
            user=henry,
            game=ark_nova,
            created_at=old_date,
        )
        stale_post_2.save()

        # Create recent sale post (should not be disabled)
        recent_post = Post(
            post_type="sale",
            text="#sell monopoly",
            active=True,
            user=marcus,
            game=monopoly,
            created_at=recent_date,
        )
        recent_post.save()

    @pytest.mark.asyncio
    async def test_cleanup_expired_posts_with_stale_posts(
        self, sample_stale_posts, mock_context, mocker
    ):
        """Tests cleanup_expired_posts disables stale posts and sends messages to users"""
        # Mock the database functions
        mock_update = mocker.patch("src.job_queues.update_and_get_stale_posts")

        # Create mock post objects
        mock_post_1 = MagicMock()
        mock_post_2 = MagicMock()

        mock_update.return_value = [mock_post_1, mock_post_2]

        # Mock game and user for each post
        mock_game_1 = MagicMock()
        mock_game_1.game_name = "Terraforming Mars"
        mock_user_1 = MagicMock()
        mock_user_1.first_name = "Jacob"
        mock_user_1.telegram_userid = 101

        mock_game_2 = MagicMock()
        mock_game_2.game_name = "Ark Nova"
        mock_user_2 = MagicMock()
        mock_user_2.first_name = "Henry"
        mock_user_2.telegram_userid = 102

        # Assign game and user to each post
        mock_post_1.game = mock_game_1
        mock_post_1.user = mock_user_1
        mock_post_2.game = mock_game_2
        mock_post_2.user = mock_user_2

        # Execute the job
        await cleanup_expired_posts(mock_context)

        # Assert update_and_get_stale_posts was called with correct cutoff time
        assert mock_update.called
        call_args = mock_update.call_args[0][0]
        assert isinstance(call_args, datetime.datetime)

        # Assert send_message was called twice for each stale post
        assert mock_context.bot.send_message.call_count == 2

        # Verify the first call
        first_call = mock_context.bot.send_message.call_args_list[0]
        assert first_call[1]["chat_id"] == 101
        assert "Terraforming Mars" in first_call[1]["text"]
        assert "Jacob" in first_call[1]["text"]
        assert first_call[1]["parse_mode"] == "Markdown"

        # Verify the second call
        second_call = mock_context.bot.send_message.call_args_list[1]
        assert second_call[1]["chat_id"] == 102
        assert "Ark Nova" in second_call[1]["text"]
        assert "Henry" in second_call[1]["text"]
        assert second_call[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_cleanup_expired_posts_no_stale_posts(self, mock_context, mocker):
        """Tests cleanup_expired_posts logs and exits when no stale posts are found"""
        # Mock the database function to return empty list
        mock_update = mocker.patch("src.job_queues.update_and_get_stale_posts")
        mock_update.return_value = []

        # Mock logging
        mock_log = mocker.patch("src.job_queues.log")

        # Execute the job
        await cleanup_expired_posts(mock_context)

        # Assert that update_and_get_stale_posts was called
        assert mock_update.called

        # Assert that send_message was not called
        assert mock_context.bot.send_message.call_count == 0

        # Assert that info message was logged
        mock_log.info.assert_called_once_with("No rows to clean today")

    @pytest.mark.asyncio
    async def test_cleanup_expired_posts_cutoff_calculation(self, mock_context, mocker):
        """Tests that cleanup_expired_posts calculates the correct cutoff date"""
        mock_update = mocker.patch("src.job_queues.update_and_get_stale_posts")
        mock_update.return_value = []

        now = datetime.datetime.now(datetime.timezone.utc)

        await cleanup_expired_posts(mock_context)

        # Get the cutoff_time passed to update_and_get_stale_posts
        call_args = mock_update.call_args[0][0]

        # Calculate expected cutoff
        expected_cutoff = now - timedelta(days=SALE_EXPIRY_DAYS)

        # Allow a small time difference (1 second) due to execution time
        assert abs((call_args - expected_cutoff).total_seconds()) < 1

    @pytest.mark.asyncio
    async def test_inform_user_sends_message_with_correct_parameters(
        self, mock_context, mocker
    ):
        """Tests inform_user sends a message with correct parameters"""
        game_name = "Terraforming Mars"
        user_id = "101"
        user_name = "Jacob"

        mock_send_message = AsyncMock()

        await inform_user(game_name, user_id, user_name, mock_send_message)

        # Assert send_message was called once
        mock_send_message.assert_called_once()

        # Get call arguments
        call_kwargs = mock_send_message.call_args[1]

        # Assert correct parameters
        assert call_kwargs["chat_id"] == user_id
        assert call_kwargs["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_inform_user_message_content(self, mock_context):
        """Tests inform_user generates correct message content"""
        game_name = "Ark Nova"
        user_id = "102"
        user_name = "Henry"

        mock_send_message = AsyncMock()

        await inform_user(game_name, user_id, user_name, mock_send_message)

        # Get the message that was sent
        call_kwargs = mock_send_message.call_args[1]
        sent_message = call_kwargs["text"]

        # Generate expected message
        expected_message = generate_stale_post_message(
            user_name=user_name, game_name=game_name
        )

        # Assert message content
        assert sent_message == expected_message
        assert user_name in sent_message
        assert game_name in sent_message

    @pytest.mark.parametrize(
        argnames="game_name, user_id, user_name",
        argvalues=[
            ("Terraforming Mars", "101", "Jacob"),
            ("Ark Nova", "102", "Henry"),
            ("Wingspan", "103", "Marcus"),
            ("Everdell", "999", "Alice"),
        ],
        ids=["terraforming_mars", "ark_nova", "wingspan", "everdell"],
    )
    @pytest.mark.asyncio
    async def test_inform_user_various_games_and_users(
        self, game_name, user_id, user_name, mock_context
    ):
        """Tests inform_user works correctly with various game names and user information"""
        mock_send_message = AsyncMock()

        await inform_user(game_name, user_id, user_name, mock_send_message)

        # Assert send_message was called
        assert mock_send_message.called

        # Get call arguments
        call_kwargs = mock_send_message.call_args[1]

        # Assert parameters
        assert call_kwargs["chat_id"] == user_id
        assert game_name in call_kwargs["text"]
        assert user_name in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_cleanup_expired_posts_calls_inform_user_correctly(
        self, mock_context, mocker
    ):
        """Tests cleanup_expired_posts calls inform_user with correct game and user information"""
        # Mock database functions
        mock_update = mocker.patch("src.job_queues.update_and_get_stale_posts")
        mock_inform_user = mocker.patch(
            "src.job_queues.inform_user", new_callable=AsyncMock
        )

        # Create mock post
        mock_post = MagicMock()
        mock_update.return_value = [mock_post]

        # Create mock game and user
        mock_game = MagicMock()
        mock_game.game_name = "Lost Ruins of Arnak"
        mock_user = MagicMock()
        mock_user.first_name = "Sarah"
        mock_user.telegram_userid = 999

        # Assign game and user to post
        mock_post.game = mock_game
        mock_post.user = mock_user

        # Execute the job
        await cleanup_expired_posts(mock_context)

        # Verify inform_user was called with correct parameters
        mock_inform_user.assert_called_once_with(
            "Lost Ruins of Arnak", 999, "Sarah", mock_context.bot.send_message
        )

    @pytest.mark.asyncio
    async def test_cleanup_expired_posts_continues_on_error(self, mock_context, mocker):
        """Tests cleanup_expired_posts continues processing posts even when inform_user fails"""
        # Mock database functions
        mock_update = mocker.patch("src.job_queues.update_and_get_stale_posts")
        mock_inform_user = mocker.patch(
            "src.job_queues.inform_user", new_callable=AsyncMock
        )
        mock_log_error = mocker.patch("src.job_queues.log.error")

        # Create two mock posts
        mock_post_1 = MagicMock()
        mock_post_2 = MagicMock()
        mock_update.return_value = [mock_post_1, mock_post_2]

        # Create mock game and user for each post
        mock_game_1 = MagicMock()
        mock_game_1.game_name = "Catan"
        mock_user_1 = MagicMock()
        mock_user_1.first_name = "Alice"
        mock_user_1.telegram_userid = 111

        mock_game_2 = MagicMock()
        mock_game_2.game_name = "Ticket to Ride"
        mock_user_2 = MagicMock()
        mock_user_2.first_name = "Bob"
        mock_user_2.telegram_userid = 222

        # Assign game and user to each post
        mock_post_1.game = mock_game_1
        mock_post_1.user = mock_user_1
        mock_post_2.game = mock_game_2
        mock_post_2.user = mock_user_2

        # Make inform_user raise an exception for the first post
        mock_inform_user.side_effect = [
            Exception("User has blocked the bot"),
            None,  # Second call succeeds
        ]

        # Execute the job
        await cleanup_expired_posts(mock_context)

        # Verify inform_user was called twice despite the first call failing
        assert mock_inform_user.call_count == 2

        # Verify logging.error was called for the failed post
        assert mock_log_error.called
        error_call_args = mock_log_error.call_args[0]
        assert "111" in str(error_call_args[1])  # User ID
        assert "Catan" in str(error_call_args[2])  # Game name

    @pytest.mark.parametrize(
        "input_text, expected_output",
        [
            ("hello", "hello"),
            ("hello_world", "hello\\_world"),
            ("*bold*", "\\*bold\\*"),
            ("[link]", "\\[link\\]"),
            ("(text)", "\\(text\\)"),
            ("hello~world", "hello\\~world"),
            ("`code`", "\\`code\\`"),
            (">quote", "\\>quote"),
            ("#hashtag", "\\#hashtag"),
            ("a+b", "a\\+b"),
            ("a-b", "a\\-b"),
            ("a=b", "a\\=b"),
            ("a|b", "a\\|b"),
            ("{text}", "\\{text\\}"),
            ("hello.world", "hello\\.world"),
            ("what!", "what\\!"),
            ("스플렌더: Pokémon (Splendor: Pokémon)", "스플렌더: Pokémon \\(Splendor: Pokémon\\)"),
            ("a_b*c[d]", "a\\_b\\*c\\[d\\]"),
            ("all!chars@#$%_*[]()~`>#+-=|{}.!test", "all\\!chars@\\#$%\\_\\*\\[\\]\\(\\)\\~\\`\\>\\#\\+\\-\\=\\|\\{\\}\\.\\!test"),
        ],
        ids=[
            "no_special_chars",
            "underscore",
            "asterisks",
            "square_brackets",
            "parentheses",
            "tilde",
            "backtick",
            "greater_than",
            "hash",
            "plus",
            "minus",
            "equals",
            "pipe",
            "curly_braces",
            "period",
            "exclamation",
            "korean_and_parens",
            "multiple_chars",
            "all_chars",
        ],
    )
    def test_escape_markdown_reserved_chars(self, input_text, expected_output):
        """Tests escape_markdown_reserved_chars properly escapes all markdown reserved characters"""
        from src.job_queues import escape_markdown_reserved_chars

        result = escape_markdown_reserved_chars(input_text)
        assert result == expected_output

    @pytest.mark.asyncio
    async def test_generate_daily_summary(self, database, mock_context, mocker):
        """Tests generate_daily_summary calls generate_summary with DAILY_SUMMARY_WINDOW"""
        mock_generate_summary = mocker.patch(
            "src.job_queues.generate_summary", new_callable=AsyncMock
        )

        from src.constants import DAILY_SUMMARY_WINDOW

        await generate_daily_summary(mock_context)

        mock_generate_summary.assert_called_once()
        call_args = mock_generate_summary.call_args[0]
        assert call_args[0] == DAILY_SUMMARY_WINDOW
        assert call_args[1] == mock_context

    @pytest.mark.asyncio
    async def test_generate_weekly_summary(self, database, mock_context, mocker):
        """Tests generate_weekly_summary calls generate_summary with WEEKLY_SUMMARY_WINDOW"""
        mock_generate_summary = mocker.patch(
            "src.job_queues.generate_summary", new_callable=AsyncMock
        )

        from src.constants import WEEKLY_SUMMARY_WINDOW

        await generate_weekly_summary(mock_context)

        mock_generate_summary.assert_called_once()
        call_args = mock_generate_summary.call_args[0]
        assert call_args[0] == WEEKLY_SUMMARY_WINDOW
        assert call_args[1] == mock_context

    @pytest.mark.asyncio
    async def test_generate_summary_no_posts(self, database, mock_context, mocker):
        """Tests generate_summary logs and exits when no posts are found"""
        mock_log = mocker.patch("src.job_queues.log")
        mocker.patch("src.job_queues.read_posts", return_value=[])

        from src.constants import DAILY_SUMMARY_WINDOW
        from src.job_queues import generate_summary

        await generate_summary(DAILY_SUMMARY_WINDOW, mock_context)

        # Assert send_message was not called
        assert mock_context.bot.send_message.call_count == 0

        # Assert logging was called
        assert mock_log.info.called

    @pytest.mark.asyncio
    async def test_generate_summary_with_posts(self, database, mock_context, mocker):
        """Tests generate_summary formats and sends summary message with posts"""
        # Create mock posts
        mock_user_1 = MagicMock()
        mock_user_1.first_name = "Alice"

        mock_user_2 = MagicMock()
        mock_user_2.first_name = "Bob"

        mock_game_1 = MagicMock()
        mock_game_1.game_name = "Catan"

        mock_game_2 = MagicMock()
        mock_game_2.game_name = "Ticket to Ride"

        mock_post_1 = MagicMock()
        mock_post_1.text = "#sell Catan"
        mock_post_1.game = mock_game_1
        mock_post_1.user = mock_user_1

        mock_post_2 = MagicMock()
        mock_post_2.text = "#auction Ticket to Ride"
        mock_post_2.game = mock_game_2
        mock_post_2.user = mock_user_2

        mock_read_posts = mocker.patch(
            "src.job_queues.read_posts", return_value=[mock_post_1, mock_post_2]
        )
        mocker.patch(
            "src.job_queues.get_summary_message_header",
            return_value="*Weekly Summary*: header\n",
        )

        from src.constants import WEEKLY_SUMMARY_WINDOW
        from src.job_queues import generate_summary

        await generate_summary(WEEKLY_SUMMARY_WINDOW, mock_context)

        # Verify send_message was called once
        assert mock_context.bot.send_message.call_count == 1

        # Get the sent message
        call_kwargs = mock_context.bot.send_message.call_args[1]
        message_text = call_kwargs["text"]
        parse_mode = call_kwargs["parse_mode"]

        # Assert message contains header
        assert "*Weekly Summary*: header" in message_text

        # Assert message contains game names and user names
        assert "Catan" in message_text
        assert "Ticket to Ride" in message_text
        assert "Alice" in message_text
        assert "Bob" in message_text

        # Assert parse mode is MarkdownV2
        assert parse_mode == "MarkdownV2"

        # Assert read_posts was called with correct parameters
        call_args = mock_read_posts.call_args[1]
        assert call_args["is_active"] is True
        assert call_args["post_type"] == "sale"

    @pytest.mark.asyncio
    async def test_generate_summary_escapes_special_characters(
        self, database, mock_context, mocker
    ):
        """Tests generate_summary escapes all special characters in game names and user names"""
        # Create mock post with special characters
        mock_user = MagicMock()
        mock_user.first_name = "User_With*Chars"

        mock_game = MagicMock()
        mock_game.game_name = "Game-With[Special]Chars"

        mock_post = MagicMock()
        mock_post.text = "#sell Test"
        mock_post.game = mock_game
        mock_post.user = mock_user

        mocker.patch("src.job_queues.read_posts", return_value=[mock_post])
        mocker.patch(
            "src.job_queues.get_summary_message_header",
            return_value="Header\n",
        )

        from src.constants import DAILY_SUMMARY_WINDOW
        from src.job_queues import generate_summary

        await generate_summary(DAILY_SUMMARY_WINDOW, mock_context)

        # Get the sent message
        call_kwargs = mock_context.bot.send_message.call_args[1]
        message_text = call_kwargs["text"]

        # Assert special characters are escaped
        assert "\\_" in message_text or "User_With*Chars" not in message_text
        assert "\\[" in message_text or "[" not in message_text

    @pytest.mark.asyncio
    async def test_generate_summary_calls_read_posts_with_correct_window(
        self, database, mock_context, mocker
    ):
        """Tests generate_summary passes correct date range to read_posts"""
        mock_read_posts = mocker.patch("src.job_queues.read_posts", return_value=[])
        mocker.patch("src.job_queues.log")

        from src.constants import DAILY_SUMMARY_WINDOW
        from src.job_queues import generate_summary

        await generate_summary(DAILY_SUMMARY_WINDOW, mock_context)

        # Verify read_posts was called
        assert mock_read_posts.called

        # Get call arguments
        call_kwargs = mock_read_posts.call_args[1]

        # Assert start_date is approximately DAILY_SUMMARY_WINDOW days ago
        now = datetime.datetime.now()
        expected_start_date = now - timedelta(days=DAILY_SUMMARY_WINDOW)

        # Allow 1 second difference due to execution time
        time_diff = abs(
            (call_kwargs["start_date"] - expected_start_date).total_seconds()
        )
        assert time_diff < 1
