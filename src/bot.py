"""Entry point for telegram bot"""

import datetime
import json
import logging
import os
from boardgamegeek import BGGClient, CacheBackendMemory  # type: ignore
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler
from src.error_handler import error_handler_cb
from src.job_queues import (
    cleanup_expired_posts,
    generate_daily_summary,
    generate_weekly_summary,
)
from src.message_handlers import message_handler
from src.command_handlers import (
    get_logs,
    start_command,
    disable_command,
    list_all_active_sales,
    list_all_active_searches,
    list_my_active_posts,
    add_bgg_username,
    disable_user,
    match_me,
    disable_post_for_user,
)
from src.models import db
from src.database import init_tables

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("./log/bot_logging.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger(__name__)


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
    app.add_handler(CommandHandler("disable_post_for_user", disable_post_for_user))
    app.add_handler(CommandHandler("match_me", match_me))
    app.add_handler(CommandHandler("get_logs", get_logs))

    # Generate the message handler with the bgg client so bgg_client doesn't get re-initialised on each message
    message_handler_with_client = init_message_handler()
    # message handlers
    app.add_handler(MessageHandler(filters=None, callback=message_handler_with_client))

    app.add_error_handler(error_handler_cb)

    # Run a daily cleanup at midnight in the bots default timezone
    app.job_queue.run_daily(callback=cleanup_expired_posts, time=datetime.time())

    # Generate daily summary on all days except sunday at 9:30AM IST
    app.job_queue.run_daily(
        callback=generate_daily_summary,
        days=[0, 1, 2, 3, 4, 5],
        time=datetime.time(hour=4, tzinfo=datetime.timezone.utc),
    )
    # Generate weekly summary every sunday at 9:30AM IST
    app.job_queue.run_daily(
        callback=generate_weekly_summary,
        days=[6],
        time=datetime.time(hour=4, tzinfo=datetime.timezone.utc),
    )
    return app


def init_message_handler():
    """Returns the message handler with the bgg_client injected. Allows easier testing"""
    bgg_client = BGGClient(
        cache=CacheBackendMemory(ttl=3600 * 24),
        timeout=30,
        retries=5,
        access_token=os.getenv("BGG_BEARER"),
    )

    async def handler(update, context):
        await message_handler(update, context, bgg_client)

    return handler


if __name__ == "__main__":
    with open("auth.json", mode="r", encoding="utf-8") as f:
        token = json.load(f)["TOKEN"]
        meeple_app = init_app(token)
        log.info("Bot is ready!")
        meeple_app.run_polling(10)
