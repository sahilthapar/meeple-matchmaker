import telegram.ext.filters
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler
from src.message_handlers import message_handler
from src.command_handlers import (start_command, disable_command,
                                  list_all_active_sales, list_all_active_searches, list_my_active_posts)
import json
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("meeple-matchmaker")


if __name__ == "__main__":
    with open('auth.json') as f:
        token = json.load(f)["TOKEN"]
        app = ApplicationBuilder().token(token).build()

        # command handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("disable", disable_command))
        app.add_handler(CommandHandler("list_all_sales", list_all_active_sales))
        app.add_handler(CommandHandler("list_all_searches", list_all_active_searches))
        app.add_handler(CommandHandler("list_my_posts", list_my_active_posts))

        # message handlers
        app.add_handler(MessageHandler(filters=None, callback=message_handler))

        log.info("Bot is ready!")
        app.run_polling()