"""Stores all functions that will be executed as repeatable job queues"""

import datetime
import logging
from src.constants import SALE_EXPIRY_DAYS
from src.database import (
    update_and_get_stale_posts,
    get_game_from_post,
    get_user_from_post,
)
from src.messages import generate_stale_post_message

log = logging.getLogger("meeple-matchmaker")


async def cleanup_expired_posts(context):
    """
    Job Queue that when executed, disables all sale posts older than SALE_EXPIRY_DAYS from today.
    """
    now = datetime.datetime.now()
    cutoff_time = now - datetime.timedelta(days=SALE_EXPIRY_DAYS)

    updated_rows = update_and_get_stale_posts(cutoff_time)

    if len(updated_rows) == 0:
        log.info("No rows to clean today")
        return

    # Iterate through the updated rows to send a DM to each person who has posted
    for post in updated_rows:
        game_name_from_post = get_game_from_post(post).game_name
        user_from_post = get_user_from_post(post)
        await inform_user(
            game_name_from_post,
            user_from_post.telegram_userid,
            user_from_post.first_name,
            context.bot.send_message,
        )


async def inform_user(game_name: str, user_id, user_name: str, send_message):
    """Sends a message to the user that their post for a game was disabled"""
    await send_message(
        chat_id=user_id,
        text=generate_stale_post_message(user_name=user_name, game_name=game_name),
        parse_mode="Markdown",
    )
