import textwrap
import sqlite3
import logging
from typing import Tuple, Optional
from boardgamegeek import BGGClient, CacheBackendMemory, BGGApiError
from telegram.constants import ChatType
from sqlite3 import Cursor

from src.database import disable_posts, read_user_posts, update_game_name

log = logging.getLogger("meeple-matchmaker")

def format_post(cursor: Cursor, post: tuple, bgg_client: BGGClient) -> str:
    game_id = post[1]
    text = post[2]
    user_id = post[3]
    user_name = post[4]
    game_name = post[5]
    if not game_name:
        log.warning("Game name not found in database, searching BGG")
        game = None
        try:
            game = bgg_client.game(game_id=game_id)
        except BGGApiError:
            log.error(f"text: {text}")
            log.error(f"game_id: {game_id}")
            log.error(f"BGGAPIError")
        if game:
            game_name = game.name
            # todo: update game name in the entire database
            update_game_name(cursor, game.id, game.name)

    return f"{game_name}: [{user_name}](tg://user?id={user_id})"

def format_list_of_posts(cursor: Cursor, posts: list[Tuple]) -> str:
    bgg_client = BGGClient(cache=CacheBackendMemory(ttl=3600 * 24 * 7))
    active_sales = list(filter(lambda x: x[1] is not None and x[0] == 'sale', posts))
    active_searches = list(filter(lambda x: x[1] is not None and x[0] == 'search', posts))

    sale_count = len(active_sales)
    search_count = len(active_searches)
    max_count = max(sale_count, search_count)
    for i in range(0, max_count, 100):

        formatted_sales = ""
        formatted_searches = ""

        if active_sales:
            formatted_sales = "\nActive sales:\n" + "\n".join(
                [format_post(cursor, x, bgg_client) for x in active_sales[i:min(i+100, sale_count)]]
            )
        if active_searches:
            formatted_searches = "\nActive searches:\n" + "\n".join(
                [format_post(cursor, x, bgg_client) for x in active_searches[i:min(i+100, search_count)]]
            )
        reply = f"{formatted_sales}\n{formatted_searches}"
        yield textwrap.dedent(reply)

async def start_command(update, context):
    """Send a message when the command /start is issued."""
    reply = """
    
    Hi, this is the meeple matchmaker bot.
    
    I'm here to help match buyers and sellers in the Meeple Market Telegram Channel
        
    *How does it work?*
    
    The bot uses two things from a posted message in the group
    
    - a message tag, supported tags are: #lookingfor, #sale, #selling, #seekinginterest, #sell, #found, #sold
    - a game name, the more accurately your name matches the BGG name, the better your chances of success
        
    Example:
    
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
    
    *How do I stop the notifications?*
    You can use messages to do this for specific games
    
    This command will remove you from the user list who are actively searching for Ark Nova
    ```
    #found Ark Nova
    ``` 
    
    This command will remove you from the user list who are actively selling Ark Nova
    ```
    #sold Ark Nova
    ``` 
    
    In addition, if you'd like to stop notifications for all posts
    Go to the bot chat and type /disable
    This will stop all tags for you for all games you've already posted about.
    *Note:* This does not stop future notifications you might sign up for again
    
    
    *Please do not post any feedback / comments / suggestions / bugs / requests on the Meeple Market Channel
    Use the chit chat channel or [Github](https://github.com/sahilthapar/meeple-matchmaker)*
    """
    if update.effective_chat.type == ChatType.GROUP:
        await update.message.set_reaction("👎")
    else:
        await update.message.reply_text(textwrap.dedent(reply), parse_mode="Markdown")

async def disable_command(update, context):
    log.info("/disable")
    conn = sqlite3.connect("database/meeple-matchmaker.db")
    user_id = update.message.from_user.id
    with conn:
        cur = conn.cursor()
        disable_posts(cur, user_id, post_type=None, game_id=None)
        conn.commit()

    conn.close()

async def list_all_active_sales(update, context):
    log.info("/list_all_sales")
    if update.effective_chat.type == ChatType.GROUP:
        await update.message.set_reaction("👎")
    else:
        conn = sqlite3.connect("database/meeple-matchmaker.db")
        with conn:
            cur = conn.cursor()
            cur.arraysize = 100
            data = read_user_posts(cur, user_id=None, post_type="sale")
            reply = format_list_of_posts(cur, data)
            for part in reply:
                conn.commit()
                await update.message.reply_text(part, parse_mode="Markdown")
        conn.close()

async def list_all_active_searches(update, context):
    log.info("/list_all_searches")
    if update.effective_chat.type == ChatType.GROUP:
        await update.message.set_reaction("👎")
    else:
        conn = sqlite3.connect("database/meeple-matchmaker.db")
        with conn:
            cur = conn.cursor()
            cur.arraysize = 100
            data = read_user_posts(cur, user_id=None, post_type="search")
            reply = format_list_of_posts(cur, data)
            for part in reply:
                conn.commit()
                await update.message.reply_text(part, parse_mode="Markdown")
        conn.close()

async def list_my_active_posts(update, context):
    log.info("/list_all_searches")
    if update.effective_chat.type == ChatType.GROUP:
        await update.message.set_reaction("👎")
    else:
        conn = sqlite3.connect("database/meeple-matchmaker.db")
        with conn:
            cur = conn.cursor()
            cur.arraysize = 100
            user_id = update.message.from_user.id
            data = read_user_posts(cur, user_id=user_id, post_type=None)
            conn.commit()
            reply = format_list_of_posts(cur, data)
            await update.message.reply_text(reply, parse_mode="Markdown")
        conn.close()
