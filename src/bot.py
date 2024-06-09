import telegram.ext.filters
from telegram.ext import ApplicationBuilder, MessageHandler
from src.handlers import message_handler
import json


if __name__ == "__main__":
    with open('auth.json') as f:
        token = json.load(f)["TOKEN"]

        app = ApplicationBuilder().token(token).build()
        app.add_handler(MessageHandler(telegram.ext.filters.TEXT, message_handler))
        app.run_polling()