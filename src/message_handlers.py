import logging
import sqlite3
from types import SimpleNamespace
from typing import Optional

from telegram.ext import ContextTypes
from telegram import Update


from src.telegrampost import parse_message
from src.database import write_to_post_db, read_post_db, disable_posts

log = logging.getLogger("meeple-matchmaker")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect("database/meeple-matchmaker.db")

    with conn:

        log.info("Attempting to parse message")
        post = parse_message(update.message) if update.message else None
        if not post:
            return
        if post.post_type == "search" and update.message:
            reply = search_message_handler(conn, post)
            if reply:
                await update.message.reply_text(reply, parse_mode='Markdown')

        elif post.post_type == "sale" and update.message:
            reply = sale_message_handler(conn, post)
            if reply:
                await update.message.reply_text(reply, parse_mode='Markdown')

        elif post.post_type == "sold" and update.message:
            sold_message_handler(conn, post)

        elif post.post_type == "found" and update.message:
            found_message_handler(conn, post)

        if post.game_id:
            await update.message.set_reaction("👍")

    conn.close()

def search_message_handler(conn: sqlite3.Connection, post: SimpleNamespace) -> Optional[str]:
    cur = conn.cursor()
    write_to_post_db(cur, [post])
    conn.commit()
    search_posts = read_post_db(cursor=cur, game_id=post.game_id, post_type="sale")
    if search_posts:
        return ', '.join([f'[{row[1]}](tg://user?id={row[0]})' for row in search_posts])
    return None

def sale_message_handler(conn: sqlite3.Connection, post: SimpleNamespace) -> Optional[str]:
    cur = conn.cursor()
    write_to_post_db(cur, [post])
    conn.commit()
    search_posts = read_post_db(cursor=cur, game_id=post.game_id, post_type="search")
    if search_posts:
        return ', '.join([f'[{row[1]}](tg://user?id={row[0]})' for row in search_posts])
    return None

def sold_message_handler(conn: sqlite3.Connection, post: SimpleNamespace) -> None:
    cur = conn.cursor()
    disable_posts(cur, post.user_id, "sale", post.game_id)
    conn.commit()

def found_message_handler(conn: sqlite3.Connection, post: SimpleNamespace) -> None:
    cur = conn.cursor()
    disable_posts(cur, post.user_id, "search", post.game_id)
    conn.commit()
