"""Stores all functions that will be executed as repeatable job queues"""

import datetime
import logging

from telegram.ext import CallbackContext
from src.constants import MEEPLE_MARKET_CHAT_ID, SALE_EXPIRY_DAYS, SUMMARY_WINDOW
from src.database import read_posts, update_and_get_stale_posts
from src.messages import generate_stale_post_message
from src.telegrampost import parse_tag

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
            log.error("Failed to send expiry notification to user %d for game %s: %s"
            , post.user.telegram_userid, post.game.game_name, e)


async def inform_user(game_name: str, user_id, user_name: str, send_message):
    """Sends a message to the user that their post for a game was disabled"""
    await send_message(
        chat_id=user_id,
        text=generate_stale_post_message(user_name=user_name, game_name=game_name),
        parse_mode="Markdown",
    )

async def generate_daily_summary(context:CallbackContext):
    """Get all active posts from the past 48hrs. Create a message with sell type, game name, and user."""
    now = datetime.datetime.now()
    time_48_hrs_ago = now - datetime.timedelta(days=SUMMARY_WINDOW)
    posts = read_posts(start_date=time_48_hrs_ago, is_active=True, post_type="sale")
    if len(posts)==0:
        log.info("No posts to summarize from the past %s days", SUMMARY_WINDOW)
        return

    final_table = ""
    for post in posts:
        final_table+=f"\n{escape_markdown_reserved_chars(parse_tag(post.text))} {escape_markdown_reserved_chars(post.game.game_name)} {escape_markdown_reserved_chars(post.user.first_name)}"

    final_table = f"*Daily Summary*: {now.strftime("%d/%m/%Y")}" + "\nThe following games were posted in the past 48 hours and are still available\n" + final_table

    log.info("%s",final_table)
    await context.bot.send_message(chat_id=MEEPLE_MARKET_CHAT_ID, text=final_table, parse_mode="MarkdownV2")

def escape_markdown_reserved_chars(text:str)->str:
    """Remove characters that are reserved by markdown from the input text"""
    text = text.replace("(", r"\(")
    text = text.replace(")", r"\)")
    text = text.replace("#", r"\#")
    text = text.replace("_", r"\_")
    text = text.replace("~", r"\~")
    text = text.replace("[", r"\[")
    text = text.replace("]", r"\]")
    return text