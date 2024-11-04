"""Handler for telegram bot commands"""
import textwrap
import logging
from typing import Iterable
from src.models import Post, UserCollection, Game
from src.telegrampost import create_user_from_message, get_bgg_username_from_message

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

    return f"{game_name}: [{user_name}](tg://user?id={user_id})"

def format_list_of_posts(posts: Iterable[Post]) -> str:
    """
    Wrapper method to format a list of message posts for replying on telegram
    :param posts:
    :return:
    """
    bgg_client = BGGClient(cache=CacheBackendMemory(ttl=3600 * 24 * 7))
    active_sales = list(filter(lambda x: x.game is not None and x.post_type == 'sale', posts))
    active_searches = list(filter(lambda x: x.game is not None and x.post_type == 'search', posts))

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
    
    Hi, this is the meeple matchmaker bot.
    
    I'm here to help match buyers and sellers in the Meeple Market Telegram Channel
        
    *How does it work?*
    
    The bot uses two things from a posted message in the group
      
    1. *a hash tag*, supported tags are:
    
      - to search for a game: *#lookingfor, #iso, #looking*
      
      - to sell a game: *#seekinginterest, #auction, #sale, #sell, #selling*
      
    2. *a game name*, the more accurately your name matches the BGG name, the better your chances of success
    
    This game name is then searched against BGG, and converted to a game id, if a successful match is found.
    
    If the bot was able to find a successful match, it will react to the message with a 👍
    
    *Important: Keep the first line of your message limited to only these two things a hashtag and a game name (as seen on BGG).
    All other details like condition, price, location should be present only in a new line*
    
    *Example:*
    
    Deepak posts a message
    ```
    #lookingfor Ark Nova
    ```
    Chaitanya posts a message
    ```
    #lookingfor Ark Nova
    ```
    Tanuj posts a message a few days later
    ```
    #seekinginterest Ark Nova
    ```
    The bot will reply to Tanuj's message and tag Deepak and Chaitanya
    ```
    @Deepak @Chaitanya
    ```
    
    *Have questions?*
    [Check out this FAQ](https://github.com/sahilthapar/meeple-matchmaker/blob/main/faq.md)
    
    *Have suggestions?*
    Use the meeple-market chit chat group
    or [Github issues](https://github.com/sahilthapar/meeple-matchmaker/issues).
    **Do not post in the main channel.**
    """
    if update.effective_chat.type == ChatType.GROUP:
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
    if update.effective_chat.type == ChatType.GROUP:
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
    user = create_user_from_message(update.message)
    bgg_username = get_bgg_username_from_message(update.message)

    user.bgg_username = bgg_username
    user.save()

    # if update.effective_chat.type != "private":
    #     await update.message.set_reaction("👎")
    await update.message.set_reaction("👍")


def get_status_from_bgg_game(game: CollectionBoardGame) -> str:
    if game.for_trade:
        return 'sale'

    if game.want_to_buy or game.wishlist:
        return 'search'

async def import_my_bgg_collection(update, _):
    # find user's bgg username
    # raise exception if no bgg username exists
    user = create_user_from_message(update.message)
    if not user.bgg_username:
        await update.message.reply_text(
            "No BGG username found! Please attach a BGG User using the command /add_bgg_username"
        )
        await update.message.set_reaction("👎")

        raise KeyError("No BGG username found! Please attach a BGG User")
    # post a request to bgg to get a user's collection
    bgg_client = BGGClient(cache=CacheBackendMemory(ttl=3600 * 24 * 7))

    bgg_collection = bgg_client.collection(user_name=user.bgg_username)
    # create a UserCollection model from it
    # insert into the post table every "for trade", "wishlist" item

    for item in bgg_collection.items:
        game_id = item.id
        game_name = item.name
        game, _ = Game.get_or_create(game_id=game_id)
        game.game_name = game_name
        game.save()
        user_collection, _ = UserCollection.get_or_create(
            user=user,
            game=game
        )
        status = get_status_from_bgg_game(item)
        if not status:
            continue
        user_collection.status = status
        user_collection.save()

        post, _ = Post.get_or_create(
            post_type=user_collection.status,
            user=user,
            game=game
        )
        post.active = True
        post.save()
    await update.message.set_reaction("👍")
    # todo: add a new command to "match me" that will respond with all possible matches sales or searches
