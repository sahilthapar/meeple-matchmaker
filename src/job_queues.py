"""Stores all functions that will be executed as repeatable job queues"""

import datetime
import logging

from telegram.ext import CallbackContext
from src.constants import (
    MEEPLE_MARKET_CHAT_ID,
    SALE_EXPIRY_DAYS,
    DAILY_SUMMARY_WINDOW,
    WEEKLY_SUMMARY_WINDOW,
)
from src.database import read_posts, update_and_get_stale_posts
from src.messages import generate_stale_post_message, get_summary_message_header

log = logging.getLogger("meeple-matchmaker")


async def cleanup_expired_posts(context):
    """
    Job Queue that when executed, disables all sale posts older than SALE_EXPIRY_DAYS from today.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff_time = now - datetime.timedelta(days=SALE_EXPIRY_DAYS)

    updated_rows = update_and_get_stale_posts(cutoff_time)

    if len(updated_rows) == 0:
        log.info("No rows to clean today")
        return

    # Iterate through the updated rows to send a DM to each person who has posted
    for post in updated_rows:
        try:
            game_name_from_post = post.game.game_name
            user_from_post = post.user
            await inform_user(
                game_name_from_post,
                user_from_post.telegram_userid,
                user_from_post.first_name,
                context.bot.send_message,
            )
        except Exception as e:
            log.error(
                "Failed to send expiry notification to user %d for game %s: %s",
                post.user.telegram_userid,
                post.game.game_name,
                e,
            )


async def inform_user(game_name: str, user_id, user_name: str, send_message):
    """Sends a message to the user that their post for a game was disabled"""
    await send_message(
        chat_id=user_id,
        text=generate_stale_post_message(user_name=user_name, game_name=game_name),
        parse_mode="Markdown",
    )


async def generate_daily_summary(context: CallbackContext):
    """Get all active posts from the past 48hrs. Create a message with sell type, game name, and user."""
    await generate_summary(DAILY_SUMMARY_WINDOW, context)


async def generate_weekly_summary(context: CallbackContext):
    """Get all active posts from the past 1 week. Create a message with sell type, game name, and user."""
    await generate_summary(WEEKLY_SUMMARY_WINDOW, context)


async def generate_summary(summary_period, context: CallbackContext):
    """Get all active posts from the past start date. Create a message with sell type, game name, and user."""
    now = datetime.datetime.now()
    start_date = now - datetime.timedelta(days=summary_period)
    posts = read_posts(start_date=start_date, is_active=True, post_type="sale")

    if len(posts) == 0:
        log.info(
            "No posts to summarize from %s till today - summary window: %d",
            start_date.strftime("%d/%m/%Y"),
            summary_period,
        )
        return

    final_table = ""

    for post in posts:
        final_table += f"\n{escape_markdown_reserved_chars(post.game.game_name)} by {escape_markdown_reserved_chars(post.user.first_name)}"

    final_table = get_summary_message_header(summary_period, start_date) + final_table
    await context.bot.send_message(
        chat_id=MEEPLE_MARKET_CHAT_ID, text=final_table, parse_mode="MarkdownV2"
    )


def escape_markdown_reserved_chars(text: str) -> str:
    """Escape characters that are reserved by markdown"""
    chars_to_escape = "_*[]()~`>#+-=|{}.!"
    for char in chars_to_escape:
        text = text.replace(char, f"\\{char}")
    return text
