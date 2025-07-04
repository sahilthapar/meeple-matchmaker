"""Handler for telegram bot commands"""
import textwrap
import logging
from typing import Iterable
from src.models import Post, UserCollection, Game
from src.telegrampost import create_user_from_message, get_message_without_command
from itertools import chain

from boardgamegeek import BGGClient, CacheBackendMemory, BGGApiError
from boardgamegeek.objects.games import CollectionBoardGame
from telegram.constants import ChatType


from src.database import disable_posts, read_posts

log = logging.getLogger("meeple-matchmaker")

def format_post(post: Post, bgg_client: BGGClient) -> str:
    """
    Method to format a record for replying on telegram
    :param post:
    :param bgg_client:
    :return:
    """
    game_id = post.game.game_id
    user_id = post.user.telegram_userid
    user_name = post.user.first_name
    game_name = post.game.game_name
    if not game_name:
        log.warning("Game name not found in database, searching BGG")
        try:
            game = bgg_client.game(game_id=game_id)
        except BGGApiError:
            log.error("game_id: %s", game_id)
            log.error("BGGAPIError")

    # remove _ from game_name
    game_name = game_name.replace('_', '')
    return f"{game_name}: [{user_name}](tg://user?id={user_id})"

def format_list_of_posts(posts: Iterable[Post]) -> str:
    """
    Wrapper method to format a list of message posts for replying on telegram
    :param posts:
    :return:
    """
    bgg_client = BGGClient(cache=CacheBackendMemory(ttl=3600 * 24 * 7))
    active_sales = [x for x in posts if x.post_type == 'sale']
    active_searches = [x for x in posts if x.post_type == 'search']

    sale_count = len(active_sales)
    search_count = len(active_searches)
    max_count = max(sale_count, search_count)
    for i in range(0, max_count, 100):

        formatted_sales = ""
        formatted_searches = ""

        if active_sales:
            formatted_sales = "\nActive sales:\n" + "\n".join(
                [format_post(x, bgg_client) for x in active_sales[i:min(i+100, sale_count)]]
            )
        if active_searches:
            formatted_searches = "\nActive searches:\n" + "\n".join(
                [format_post(x, bgg_client) for x in active_searches[i:min(i+100, search_count)]]
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
    reply = """
Hi! I'm Meeple Matchmaker Bot.

I help match buyers and sellers in the Meeple Market Telegram channel.

*How to use:*
- Start your message with a hashtag and the game name (as listed on BGG).
  - To buy: #lookingfor, #iso, #looking
  - To sell: #sale, #sell, #selling, #auction, #seekinginterest
- The bot will check the game name on BGG and react with 👍 if it finds a match.

*Tip:*
Keep the first line to just the hashtag and game name. Add details (condition, price, location) on new lines.

[Full guide & features](https://github.com/sahilthapar/meeple-matchmaker/blob/main/README.md)
[FAQ](https://github.com/sahilthapar/meeple-matchmaker/blob/main/faq.md)
Suggestions? Use the chit chat group or [GitHub issues](https://github.com/sahilthapar/meeple-matchmaker/issues).
**Don't post suggestions in the main channel.**
"""
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
            await update.message.reply_text(
                "Invalid username! Add username after the command. Copy the example below."
            )
            await update.message.reply_text(
                "/add_bgg_username my-username"
            )
            await update.message.set_reaction("👎")


def get_status_from_bgg_game(game: CollectionBoardGame) -> str:
    if game.for_trade:
        return 'sale'

    if game.want_to_buy or game.wishlist:
        return 'search'

async def import_my_bgg_collection(update, _):
    """
    Handler for command /import_my_bgg_collection

    - find user's bgg username
        - raise exception if no bgg username exists
    - post a request to bgg to get a user's collection
        - create a UserCollection model from it
    - insert into the post table every "for trade", "wishlist" item
    :param update:
    :param _:
    :return:
    """
    user = create_user_from_message(update.message)
    if update.effective_chat.type != "private":
        await update.message.set_reaction("👎")
    else:
        if not user.bgg_username:
            await update.message.reply_text(
                "No BGG username found! Please attach a BGG User using the command /add_bgg_username <your-username>"
            )
            await update.message.set_reaction("👎")

            raise KeyError("No BGG username found! Please attach a BGG User")

        bgg_client = BGGClient(cache=CacheBackendMemory(ttl=3600 * 24 * 7))
        bgg_collection = bgg_client.collection(user_name=user.bgg_username)

        for item in bgg_collection.items:
            # todo: refactor all code like this into method of the class, "find_and_update"
            game_id = item.id
            game_name = item.name
            game, _ = Game.get_or_create(game_id=game_id)
            game.game_name = game_name
            game.save()
            status = get_status_from_bgg_game(item)
            if not status:
                continue
            user_collection, _ = UserCollection.get_or_create(
                user=user,
                game=game,
                status=status
            )
            user_collection.save()

            post = Post.get_or_none(
                post_type=user_collection.status,
                user=user,
                game=game,
                active=True
            )
            if not post:
                log.info(f'inserting a {status} post for {game.game_name} into the table for user {user.first_name}')
                post = Post(
                    post_type=user_collection.status,
                    user=user,
                    game=game,
                    active=True,
                    text="auto-generated from bgg-collection"
                )
                post.save()
        await update.message.set_reaction("👍")

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
    user = create_user_from_message(update.message)
    posts = read_posts(user_id=user.telegram_userid)

    user_searches = [p for p in posts if p.post_type == 'search']
    user_sales = [p for p in posts if p.post_type == 'sale']

    matched_searches = []
    matched_sales = []
    if user_searches:
        matched_searches = read_posts(game_id=[search.game.game_id for search in user_searches],
                                      post_type='sale')
    if user_sales:
        matched_sales = read_posts(game_id=[sale.game.game_id for sale in user_sales],
                                   post_type='search')

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

    if update.message.from_user.id != 995823071:
        await update.message.reply_text("Sorry this command is only available to the admin!")
        return

    user_to_disable = get_message_without_command(update.message)
    disable_posts(user_id=int(user_to_disable))
    await update.message.set_reaction("👍")
