import telegram.ext.filters
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler
from message_handlers import message_handler
from command_handlers import start_command, disable_command
import json


if __name__ == "__main__":
    with open('auth.json') as f:
        token = json.load(f)["TOKEN"]
        app = ApplicationBuilder().token(token).build()

        # command handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("disable", disable_command))

        # message handlers
        app.add_handler(MessageHandler(telegram.ext.filters.TEXT, message_handler))

        app.run_polling()