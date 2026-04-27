"""Entry point for telegram bot"""
import json
import logging
import os
from boardgamegeek import BGGClient, CacheBackendMemory  # type: ignore
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler
from src.message_handlers import message_handler
from src.command_handlers import (
    start_command, disable_command, list_all_active_sales, list_all_active_searches, list_my_active_posts,
    add_bgg_username, disable_user, import_my_bgg_collection, match_me
)
from src.models import db
from src.database import init_tables

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("meeple-matchmaker")

def init_app(auth_token):
    """Sets up the telegram app with command and message handlers"""

    app = ApplicationBuilder().token(auth_token).build()
    db.init("database/meeple-matchmaker.db")
    log.info("Connected to DB")
    # Create tables. If they exist, nothing happens
    init_tables(db)
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

    # Generate the message handler with the bgg client so bgg_client doesn't get re-initialised on each message
    message_handler_with_client = init_message_handler()
    # message handlers
    app.add_handler(MessageHandler(filters=None, callback=message_handler_with_client))

    return app

def init_message_handler():
    """Returns the message handler with the bgg_client injected. Allows easier testing"""
    bgg_client = BGGClient(cache=CacheBackendMemory(ttl=3600*24*7), access_token=os.getenv('BGG_BEARER'))
    return lambda update,_: message_handler(update,_,bgg_client)


if __name__ == "__main__":
    with open('auth.json', mode="r", encoding="utf-8") as f:
        token = json.load(f)["TOKEN"]
        meeple_app = init_app(token)
        log.info("Bot is ready!")
        meeple_app.run_polling(10)
