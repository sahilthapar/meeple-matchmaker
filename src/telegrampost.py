"""Module providing miscellaneous processing methods related to telegram posts"""

import asyncio
import re
from logging import getLogger
from typing import Optional, Tuple
from peewee import IntegrityError

from telegram import Message
from boardgamegeek import BGGApiError, BGGClient, BGGItemNotFoundError  # type: ignore

from src.constants import MAX_ATTEMPTS, MEEPLE_MARKET_CHAT_ID, SEARCH_TYPES, BGGFailed
from src.models import Game, User, Post, db

log = getLogger(__name__)


TYPE_LOOKUP = {
    "#lookingfor": "search",
    "#iso": "search",
    "#looking": "search",
    "#sale": "sale",
    "#selling": "sale",
    "#sell": "sale",
    "#auction": "sale",
    "#sold": "sold",
    "#found": "found",
}

POST_TYPES_BANNED_IN_DM = ["sale"]

POST_TYPES_BANNED_IN_GROUP = ["found"]


def get_message_contents(message: Message) -> str:
    """Extract the text or caption from a message"""
    if message is None:
        return ""
    text = message.text or message.caption
    return text.lower() if text else ""


def parse_tag(message: str) -> str:
    """Extracts the tag used in the message"""
    tag = re.search(
        pattern="^#lookingfor|^#iso|^#looking|^#sale|^#selling|^#sell|^#auction|^#sold|^#found",
        string=message,
    )
    if not tag:
        return ""
    return tag.group()


def parse_game_name(message: str) -> str:
    """Performs string replacement (if required) and returns the game name as typed by the user"""
    first_line = message.strip().split("\n")[0]
    return first_line.replace("game name:", "").replace("game:", "").strip()


async def get_game_details(game_name: str, bgg_client: BGGClient) -> Optional[Game]:
    """
    Uses the BGG Client to fetch a game based on its name.
    If found, checks the DB for an existing entry, otherwise creates the game and returns the model.
    """
    for attempt in range(MAX_ATTEMPTS):
        for search_type in SEARCH_TYPES:
            try:
                log.info("Trying %s match for game: %s", search_type, game_name)
                # todo: use .search instead of .game
                game = await asyncio.to_thread(
                    bgg_client.game, game_name, exact=search_type == "exact"
                )
                return await get_or_add_game(game, search_type=search_type)
            except BGGItemNotFoundError:
                # If we have not found the game in all search types, exit
                if search_type == SEARCH_TYPES[-1]:
                    return None
                # If the game is not found, continue into the fuzzy block
                continue
            except BGGApiError as e:
                log.warning(
                    "BGG API Failed at %s search with error %s, retrying",
                    search_type,
                    e,
                )
                # If we have exhausted attempts and still get a bgg error, inform the caller
                if attempt == MAX_ATTEMPTS - 1:
                    raise BGGFailed from e
                # Break out of this block in case we get a bggapierror
                break
            except Exception as e:
                raise e


async def get_or_add_game(game, search_type="exact"):
    """Helper function that tries to add a game to the db. If the same id exists, we catch the Integrity Error and return that game"""
    if game:
        log.info("Found %s match", search_type)
        try:
            with db.atomic():
                return Game.create(game_name=game.name, game_id=game.id)
        except IntegrityError:
            return Game.get(Game.game_id == game.id)
    return None


def create_user_from_message(message: Message) -> User:
    """
    Reads a telegram message, extracts user info and returns a User ORM
    :param message:
    :return:
    """
    user, _ = User.get_or_create(telegram_userid=message.from_user.id)
    user.first_name = message.from_user.first_name
    user.last_name = message.from_user.last_name

    return user


def get_message_without_command(message: Message) -> str:
    """Extracts the message text by deleting the first word (usually a commmand)"""
    text = get_message_contents(message)
    return text.split(" ")[1]


async def parse_message(
    message: Message, bgg_client
) -> Tuple[Optional[Post], Optional[Game], Optional[User]]:
    """
    Parses a telegram message to find details about game, user and the message
    returns ORM for Post, Game, User
    :param message:
    :return:
    """
    # parse user info
    user = create_user_from_message(message)

    # parse text
    message_text = get_message_contents(message)
    log.info(message_text)
    tag = parse_tag(message_text)
    message_without_tag = message_text.replace(tag, "").strip()
    message_type = TYPE_LOOKUP.get(tag, None)

    # if no post type found, exit
    if not message_type:
        return None, None, None

    # parse game info
    game_name = parse_game_name(message_without_tag)
    game = await get_game_details(game_name, bgg_client)
    if not game:
        log.warning("Game not found")
        return None, None, None

    post = Post(
        post_type=message_type,
        text=message_text,
        active=1,
        user=user,
        game=game,
        telegram_msg_id=message.id,
    )
    game.save()
    user.save()
    post.save()

    return post, game, user


def find_post_type(message: Message) -> Optional[str]:
    """
    Finds the post type from a message (eg: sale, found)
    """
    message_text = get_message_contents(message)
    tag = parse_tag(message_text)
    post_type = TYPE_LOOKUP.get(tag, None)
    return post_type


def is_post_type_banned(post_type: str, chat_type: str) -> bool:
    """
    True if a post type is not allowed in its specific context (DM or group)
    """
    banned_in_dm = post_type in POST_TYPES_BANNED_IN_DM and chat_type == "private"
    banned_in_group = post_type in POST_TYPES_BANNED_IN_GROUP and chat_type != "private"
    return banned_in_dm or banned_in_group


def is_from_external_chat(chat_type, chat_id) -> bool:
    """
    True if someone tries to add meeple bot to another group and send messages from there.
    We only want messages from meeple market to pass through.
    """
    if chat_type != "private" and chat_id != MEEPLE_MARKET_CHAT_ID:
        return True
    return False


def format_user_tag(username, userid):
    """Helper func that returns a markdown link to a user's profile"""
    return f"[{username}](tg://user?id={userid})"


def escape_markdown_reserved_chars(text: str) -> str:
    """Escape characters that are reserved by markdown when rendering bot messages."""
    chars_to_escape = "_*[]()~`>#+-=|{}.!"
    for char in chars_to_escape:
        text = text.replace(char, f"\\{char}")
    return text


def form_link_to_post(telegram_msg_id, text="(Post)"):
    """Helper func that returns a markdown link to a specific message in meeple market"""
    # Group Chat IDs start with '-100', but links don't use that
    chat_id_without_prefix = str(MEEPLE_MARKET_CHAT_ID)[4:]
    return f"[{text}](tg://privatepost?channel={chat_id_without_prefix}&post={telegram_msg_id})"
