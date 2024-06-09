import sqlite3

from telegram.ext import ContextTypes
from telegram import Update


from src.telegrampost import get_post
from src.database import write_to_post_db, read_post_db
from src.telegrampost import TelegramPost

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect("meeple-matchmaker")
    with conn:
        post = get_post(update.message)

        if post.post_type == "search":
            reply = search_message_handler(conn, post)
            if reply:
                await update.message.reply_text(reply, parse_mode='Markdown')

        elif post.post_type == "sale":
            reply = sale_message_handler(conn, post)
            if reply:
                await update.message.reply_text(reply, parse_mode='Markdown')

    conn.close()

def search_message_handler(conn: sqlite3.Connection, post: TelegramPost) -> str:
    cur = conn.cursor()
    write_to_post_db(cur, [post])
    conn.commit()
    search_posts = read_post_db(cursor=cur, game_id=post.game_id, post_type="sale")
    if search_posts:
        return ', '.join([f'[{row[1]}](tg://user?id={row[0]})' for row in search_posts])

def sale_message_handler(conn: sqlite3.Connection, post: TelegramPost) -> str:
    cur = conn.cursor()
    write_to_post_db(cur, [post])
    conn.commit()
    search_posts = read_post_db(cursor=cur, game_id=post.game_id, post_type="search")
    if search_posts:
        return ', '.join([f'[{row[1]}](tg://user?id={row[0]})' for row in search_posts])
