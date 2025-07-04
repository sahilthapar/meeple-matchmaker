"""Entry point for telegram bot"""
import json
import logging

from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler
from src.message_handlers import message_handler
from src.command_handlers import (
    start_command, disable_command, list_all_active_sales, list_all_active_searches, list_my_active_posts,
    add_bgg_username, disable_user, import_my_bgg_collection, match_me
)
from src.models import db


logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("meeple-matchmaker")


if __name__ == "__main__":
    with open('auth.json', mode="r", encoding="utf-8") as f:
        token = json.load(f)["TOKEN"]
        app = ApplicationBuilder().token(token).build()
        db.init("database/meeple-matchmaker.db")
        # command handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("disable", disable_command))
        app.add_handler(CommandHandler("list_all_sales", list_all_active_sales))
        app.add_handler(CommandHandler("list_all_searches", list_all_active_searches))
        app.add_handler(CommandHandler("list_my_posts", list_my_active_posts))
        app.add_handler(CommandHandler("add_bgg_username", add_bgg_username))
        app.add_handler(CommandHandler("disable_user", disable_user))
        app.add_handler(CommandHandler("import_my_bgg_collection", import_my_bgg_collection))
        app.add_handler(CommandHandler("match_me", match_me))

        # message handlers
        app.add_handler(MessageHandler(filters=None, callback=message_handler))

        log.info("Bot is ready!")
        app.run_polling(10)
