"""telegram bot handlers for specific message types"""
import logging
import sqlite3
from types import SimpleNamespace
from typing import Optional

from telegram.ext import ContextTypes
from telegram import Update

from src.telegrampost import parse_message
from src.database import write_to_post_db, read_posts, disable_posts

log = logging.getLogger("meeple-matchmaker")

async def message_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Primary message handler which passes the message to specialized handler based on the post_type
    after parsing the message
    :param update:
    :param _:
    :return:
    """

    with sqlite3.connect("database/meeple-matchmaker.db") as conn:
        log.info("Attempting to parse message")
        post, game, user = parse_message(update.message) if update.message else None
        if not post:
            return
        if update.message:
            handler = MESSAGE_HANDLERS.get(post.post_type)
            reply = handler(conn, post)
            # send reply
            if reply:
                await update.message.reply_text(reply, parse_mode='Markdown')

        if post.game_id:
            await update.message.set_reaction("👍")


def search_message_handler(conn: sqlite3.Connection, post: SimpleNamespace) -> Optional[str]:
    """
    Method to handle messages that are "searches" for games
    :param conn:
    :param post:
    :return:
    """
    cur = conn.cursor()
    write_to_post_db(cur, [post])
    conn.commit()
    search_posts = read_posts(cursor=cur, game_id=post.game_id, post_type="sale")
    if search_posts:
        return ', '.join([f'[{row[1]}](tg://user?id={row[0]})' for row in search_posts])
    return None

def sale_message_handler(conn: sqlite3.Connection, post: SimpleNamespace) -> Optional[str]:
    """
    Method to handle messages that are "selling" games
    :param conn:
    :param post:
    :return:
    """
    cur = conn.cursor()
    write_to_post_db(cur, [post])
    conn.commit()
    search_posts = read_posts(cursor=cur, game_id=post.game_id, post_type="search")
    if search_posts:
        return ', '.join([f'[{row[1]}](tg://user?id={row[0]})' for row in search_posts])
    return None

def sold_message_handler(conn: sqlite3.Connection, post: SimpleNamespace) -> None:
    """
    Method to handle messages marking game as sold
    :param conn:
    :param post:
    :return:
    """
    cur = conn.cursor()
    disable_posts(cur, post.user_id, "sale", post.game_id)
    conn.commit()

def found_message_handler(conn: sqlite3.Connection, post: SimpleNamespace) -> None:
    """
    Method to handle messages marking game as found
    :param conn:
    :param post:
    :return:
    """
    cur = conn.cursor()
    disable_posts(cur, post.user_id, "search", post.game_id)
    conn.commit()


MESSAGE_HANDLERS = {
    "search": search_message_handler,
    "sale": sale_message_handler,
    "sold": sold_message_handler,
    "found": found_message_handler
}
