"""telegram bot handlers for specific message types"""
import logging
from typing import Optional

from telegram.ext import ContextTypes
from telegram import Update

from src.telegrampost import parse_message
from src.database import read_posts, disable_posts
from src.models import Post

log = logging.getLogger("meeple-matchmaker")


COMPLEMENTARY_POST_TYPE = {
    "search": "sale",
    "sale": "search",
    "sold": "sale",
    "found": "search"
}

async def message_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Primary message handler which passes the message to specialized handler based on the post_type
    after parsing the message
    :param update:
    :param _:
    :return:
    """
    log.info("Attempting to parse message")
    post, game, user = parse_message(update.message) if update.message else (None, None, None)
    if not post or not game or not user:
        return
    if update.message:
        if post.post_type == 'search' or post.post_type == 'sale':
            reply = find_matching_posts(post)
            if reply:
                await update.message.reply_text(reply, parse_mode='Markdown')
        elif post.post_type == 'sold' or post.post_type == 'found':
            disable_post(post)

    if post.game:
        await update.message.set_reaction("👍")


def find_matching_posts(post: Post) -> Optional[str]:
    """
    Method to handle messages that are "searches" for games
    :param post:
    :return:
    """
    def _format_user_tag(username, userid):
        return f'[{username}](tg://user?id={userid})'

    post_type = COMPLEMENTARY_POST_TYPE.get(post.post_type)
    posts = read_posts(game_id=post.game.game_id, post_type=post_type)
    if posts:
        users = set()
        for post in posts:
            users.add((post.user.first_name, post.user.telegram_userid))
        return ', '.join([
            _format_user_tag(*user) for user in users
        ])
    return None


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
        game_id=post.game.game_id
    )
