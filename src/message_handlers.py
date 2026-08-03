"""telegram bot handlers for specific message types"""

import logging
from typing import Optional

from telegram.ext import ContextTypes
from telegram import Update
from boardgamegeek import BGGClient  # type: ignore

from src.constants import BGGFailed
from src.messages import BGG_DOWN_MESSAGE
from src.telegrampost import (
    form_link_to_post,
    format_user_tag,
    parse_message,
    find_post_type,
    is_post_type_banned,
    is_from_external_chat,
)
from src.database import read_posts, disable_posts
from src.models import Post

log = logging.getLogger(__name__)


COMPLEMENTARY_POST_TYPE = {
    "search": "sale",
    "sale": "search",
    "sold": "sale",
    "found": "search",
}


async def message_handler(
    update: Update, _: ContextTypes.DEFAULT_TYPE, bgg_client: BGGClient
) -> None:
    """
    Primary message handler which passes the message to specialized handler based on the post_type
    after parsing the message
    :param update:
    :param _:
    :return:
    """
    log.info(
        "chat_id=%s type=%s title=%s",
        update.effective_chat.id,
        update.effective_chat.type,
        update.effective_chat.title,
    )
    # Check if message is a valid command before trying to hit the API
    post_type = find_post_type(update.message)

    if not post_type:
        return

    should_ignore_post = is_post_type_banned(
        post_type, update.effective_chat.type
    ) or is_from_external_chat(update.effective_chat.type, update.effective_chat.id)

    if should_ignore_post:
        await update.message.set_reaction("👎")
        return

    log.info("Attempting to parse message")

    try:
        post, game, user = (
            await parse_message(update.message, bgg_client)
            if update.message
            else (None, None, None)
        )
    except BGGFailed:
        log.error("BGG API Failed")
        await update.message.reply_text(BGG_DOWN_MESSAGE)
        return
    if not post or not game or not user:
        await update.message.set_reaction("🤔")
        return
    if update.message:
        if post.post_type == "search" or post.post_type == "sale":
            reply = find_matching_posts(post)
            if reply:
                await update.message.reply_text(reply, parse_mode="Markdown")
        elif post.post_type == "sold" or post.post_type == "found":
            disable_post(post)

    if post.game:
        await update.message.set_reaction("👍")


def find_matching_posts(post: Post) -> Optional[str]:
    """
    Method to handle messages that are "searches" for games
    :param post:
    :return:
    """

    complementary_post_type = COMPLEMENTARY_POST_TYPE.get(post.post_type)
    matching_posts = read_posts(
        game_id=post.game.game_id,
        post_type=complementary_post_type,
    )

    rendered = [
        get_matching_post_message_contents(matching_post)
        for matching_post in matching_posts
    ]
    return ", ".join(rendered) or None


def get_matching_post_message_contents(post: Post):
    """
    Returns a markdown link to the sale post if it exists
    Else returns a link to the user's profile
    """
    contents = format_user_tag(post.user.first_name, post.user.telegram_userid)
    if post.telegram_msg_id and post.post_type == "sale":
        contents += " " + form_link_to_post(post.telegram_msg_id)
    return contents


def disable_post(post: Post) -> None:
    """
    Method to handle messages marking game as sold
    :param post:
    :return:
    """
    comp_post_type = COMPLEMENTARY_POST_TYPE.get(post.post_type)

    disable_posts(
        user_id=post.user.telegram_userid,
        post_type=comp_post_type,
        game_id=post.game.game_id,
    )
