import telegram.ext.filters
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes
from src.telegrampost import get_post
from src.database import write_to_post_db, read_post_db
import sqlite3
import json

CONN = sqlite3.connect("meeple-matchmaker")
CURSOR = CONN.cursor()

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    post = get_post(update.message)
    # if the message type is search, just insert into db
    if post.post_type == "search":
        write_to_post_db(CURSOR, [post])
        CONN.commit()
        search_posts = read_post_db(cursor=CURSOR, game_id=post.game_id, post_type="sale")
        if search_posts:
            html_msg = ', '.join([f'[{row[1]}](tg://user?id={row[0]})' for row in search_posts])
            await update.message.reply_text(html_msg, parse_mode='Markdown')

    elif post.post_type == "sale":
        write_to_post_db(CURSOR, [post])
        CONN.commit()
        search_posts = read_post_db(cursor=CURSOR, game_id=post.game_id, post_type="search")
        if search_posts:
            html_msg = ', '.join([f'[{row[1]}](tg://user?id={row[0]})' for row in search_posts])
            await update.message.reply_text(html_msg, parse_mode='Markdown')

    else:
        pass


if __name__ == "__main__":
    with open('auth.json') as f:
        token = json.load(f)["TOKEN"]

        app = ApplicationBuilder().token(token).build()
        app.add_handler(MessageHandler(telegram.ext.filters.TEXT, message_handler))
        app.run_polling()