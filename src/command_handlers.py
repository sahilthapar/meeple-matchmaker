"""Handler for telegram bot commands"""

import re
import textwrap
import logging
import os
from itertools import chain
from typing import Iterable, Generator
from boardgamegeek.objects.games import CollectionBoardGame
from telegram import Update
from src.constants import ADMIN_IDS
from src.models import Post
from src.telegrampost import (
    create_user_from_message,
    form_link_to_post,
    format_user_tag,
    get_message_without_command,
)
from src.database import disable_posts, read_posts
from src.messages import (
    INVALID_DISABLE_POST_FOR_USER,
    INVALID_NOT_AN_ADMIN,
    INVALID_DISABLE_USER,
    INVALID_ADD_BGG_USERNAME_ERROR,
    INVALID_ADD_BGG_USERNAME_SHOW_FORMAT,
    MEEPLE_MATCHMAKER_START,
)

log = logging.getLogger(__name__)


def format_post(post: Post) -> str:
    """
    Method to format a record for replying on telegram
    :param post:
    :param bgg_client:
    :return:
    """
    user_id = post.user.telegram_userid
    user_name = post.user.first_name
    game_name = post.game.game_name

    # remove _ from game_name
    game_name_md = game_name.replace("_", "")

    if post.post_type == "sale" and post.telegram_msg_id:
        game_name_md = form_link_to_post(post.telegram_msg_id, game_name_md)

    return f"{game_name_md}: {format_user_tag(user_name,user_id)}"


def format_list_of_posts(posts: Iterable[Post]) -> Generator[str, None, None]:
    """
    Wrapper method to format a list of message posts for replying on telegram
    :param posts:
    :return:
    """
    active_sales = [x for x in posts if x.post_type == "sale"]
    active_searches = [x for x in posts if x.post_type == "search"]

    sale_count = len(active_sales)
    search_count = len(active_searches)
    max_count = max(sale_count, search_count)
    for i in range(0, max_count, 100):
        formatted_sales = ""
        formatted_searches = ""

        if active_sales:
            formatted_sales = "\nActive sales:\n" + "\n".join(
                [format_post(x) for x in active_sales[i : min(i + 100, sale_count)]]
            )
        if active_searches:
            formatted_searches = "\nActive searches:\n" + "\n".join(
                [
                    format_post(x)
                    for x in active_searches[i : min(i + 100, search_count)]
                ]
            )
        reply = f"{formatted_sales}\n{formatted_searches}"
        yield textwrap.dedent(reply)


async def start_command(update, _):
    """
    Command handler for the starting / help message
    :param update:
    :param _:
    :return:
    """
    reply = MEEPLE_MATCHMAKER_START
    if update.effective_chat.type != "private":
        await update.message.set_reaction("👎")
    else:
        await update.message.reply_text(textwrap.dedent(reply), parse_mode="Markdown")


async def disable_command(update, _):
    """
    Command handler to disable all active posts for a user
    :param update:
    :param _:
    :return:
    """
    log.info("/disable")
    if update.effective_chat.type != "private":
        await update.message.set_reaction("👎")
    else:
        user_id = update.message.from_user.id
        disable_posts(user_id=user_id)


async def list_all_active_sales(update, _):
    """
    Command handler to list all active sales currently being tracked by the bot
    :param update:
    :param _:
    :return:
    """
    log.info("/list_all_sales")
    if update.effective_chat.type != "private":
        await update.message.set_reaction("👎")
    else:
        data = read_posts(post_type="sale")
        reply = format_list_of_posts(data)
        for part in reply:
            await update.message.reply_text(part, parse_mode="Markdown")


async def list_all_active_searches(update, _):
    """
    Command handler to list all active searches currently being tracked by the bot
    :param update:
    :param _:
    :return:
    """
    log.info("/list_all_searches")
    if update.effective_chat.type != "private":
        await update.message.set_reaction("👎")
    else:
        data = read_posts(post_type="search")
        reply = format_list_of_posts(data)
        for part in reply:
            await update.message.reply_text(part, parse_mode="Markdown")


async def list_my_active_posts(update, _):
    """
    Command handler to list all active posts for the user
    :param update:
    :param _:
    :return:
    """
    log.info("/list_my_posts")
    if update.effective_chat.type != "private":
        await update.message.set_reaction("👎")
    else:
        user_id = update.message.from_user.id
        data = read_posts(user_id=user_id)
        reply = format_list_of_posts(data)
        for part in reply:
            await update.message.reply_text(part, parse_mode="Markdown")


async def add_bgg_username(update, _):
    """
    Allows a user to save their bgg username in the bots DB so they can import their collection later
    """
    log.info("/add_bgg_username")
    user = create_user_from_message(update.message)
    if update.effective_chat.type != "private":
        await update.message.set_reaction("👎")
    else:
        try:
            bgg_username = get_message_without_command(update.message)
            user.bgg_username = bgg_username
            user.save()
            await update.message.set_reaction("👍")
        except IndexError:
            await update.message.reply_text(INVALID_ADD_BGG_USERNAME_ERROR)
            await update.message.reply_text(INVALID_ADD_BGG_USERNAME_SHOW_FORMAT)
            await update.message.set_reaction("👎")


def get_status_from_bgg_game(game: CollectionBoardGame) -> str:
    """
    Maps a BGG game status to a meeple-matchmaker post tag
    """
    if game.for_trade:
        return "sale"

    if game.want_to_buy or game.wishlist:
        return "search"


async def match_me(update, _):
    """
    Handler for command /match_me
    Finds through the users entire active posts
    Searches for matches for each of the games
    :param update:
    :param _:
    :return:
    """
    if update.effective_chat.type != "private":
        await update.message.set_reaction("👎")
        return
    user = create_user_from_message(update.message)
    posts = read_posts(user_id=user.telegram_userid)
    user_searches = [p for p in posts if p.post_type == "search"]
    user_sales = [p for p in posts if p.post_type == "sale"]

    matched_searches = []
    matched_sales = []
    if user_searches:
        matched_searches = read_posts(
            game_id=[search.game.game_id for search in user_searches], post_type="sale"
        )
    if user_sales:
        matched_sales = read_posts(
            game_id=[sale.game.game_id for sale in user_sales], post_type="search"
        )

    reply_sales = format_list_of_posts(matched_searches)
    reply_searches = format_list_of_posts(matched_sales)
    for part in chain(reply_searches, reply_sales):
        await update.message.reply_text(part, parse_mode="Markdown")


async def disable_user(update, _):
    """
    Takes in a request to disable a user
    Must be requested by an admin only
    :param update:
    :param _:
    :return:
    """
    if update.effective_chat.type != "private":
        await update.message.set_reaction("👎")
        return

    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text(INVALID_NOT_AN_ADMIN)
        return
    try:
        pattern = r"(?:\/disable_user)\s+(\d+)\s+(sale|search|all)$"
        match = re.match(pattern, update.message.text)
        if match is None or len(match.groups()) < 2:
            raise IndexError
        user_id, post_type = match.groups()
        # set post type to None if admin chooses all, so that the db disables all the post types for that user
        post_type = None if post_type == "all" else post_type
        disable_posts(user_id, post_type)
    except IndexError:
        await update.message.reply_text(INVALID_DISABLE_USER)
        return
    await update.message.set_reaction("👍")


async def disable_post_for_user(update, _):
    """
    Takes in a request to disable a specific post for a user
    Must be requested by an admin only
    """
    if update.effective_chat.type != "private":
        await update.message.set_reaction("👎")
        return
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text(INVALID_NOT_AN_ADMIN)
        return
    try:
        message_contents = update.message.text
        # Captures a number, a space separated string for game name, and post type as sale or search
        # pattern = r"(?:\/disable_post_for_user)\s+(\d+)\s+(.+?)\s+(sale|search)$"
        pattern = r"(?:\/disable_post_for_user)\s+(\d+)\s+(\d+)\s+(sale|search)$"
        match = re.match(pattern, message_contents)
        if match is None or len(match.groups()) < 3:
            raise IndexError
        user_id, game_id, post_type = match.groups()
        disable_posts(user_id, post_type, game_id)
        await update.message.set_reaction("👍")
    except IndexError:
        await update.message.reply_text(INVALID_DISABLE_POST_FOR_USER)


async def get_logs(update: Update, context):
    """Fetch the log file
    Must be requested by an admin only
    """
    if update.effective_chat.type != "private":
        await update.message.set_reaction("👎")
        return
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text(INVALID_NOT_AN_ADMIN)
        return
    log_file_path = "./log/bot_logging.log"

    if os.path.exists(log_file_path):
        # Send the file to the admin
        log.info("Sending logs to user %s", update.message.from_user.full_name)
        with open(log_file_path, "rb") as document:
            await context.bot.send_document(
                chat_id=update.message.from_user.id,
                document=document,
                filename="bot_export.log",
                caption="Here are your latest bot logs.",
            )
    else:
        await update.message.reply_text("Log file not found yet.")
