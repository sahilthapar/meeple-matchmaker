"""Module providing miscellaneous processing methods related to telegram posts"""

import os
import re
from logging import getLogger
from typing import Optional, Tuple

from telegram import Message
from boardgamegeek import BGGClient, BGGItemNotFoundError, CacheBackendMemory  # type: ignore

from src.models import Game, User, Post

log = getLogger()


TYPE_LOOKUP = {
    "#lookingfor": "search",
    "#iso": "search",
    "#looking": "search",
    "#sale": "sale",
    "#selling": "sale",
    "#seekinginterest": "sale",
    "#sell": "sale",
    "#auction": "sale",
    "#sold": "sold",
    "#found": "found",
}

TAGS_BANNED_IN_DM = [
    "#seekinginterest",
    "#sell"
]

TAGS_BANNED_IN_GROUP = [
    "#seekinginterest",
    "#found"
]

def get_message_contents(message: Message) -> str:
    """Extract the text or caption from a message"""
    text = message.text or message.caption
    return text.lower() if text else ""

def parse_tag(message: str) -> str:
    """Extracts the tag used in the message"""
    tag = re.search(
        pattern="^#lookingfor|^#iso|^#looking|^#sale|^#selling|^#seekinginterest|^#sell|^#auction|^#sold|^#found",
        string=message
    )
    if not tag:
        return ""
    return tag.group()

def parse_game_name(message: str) -> str:
    """Performs string replacement (if required) and returns the game name as typed by the user"""
    first_line = message.strip().split("\n")[0]
    return first_line.replace("game name:", "").replace("game:", "").strip()

def get_game_details(game_name: str, bgg_client: BGGClient) -> Optional[Game]:
    """
    Uses the BGG Client to fetch a game based on its name. 
    If found, checks the DB for an existing entry, otherwise creates the game and returns the model.
    """
    try:
        log.info("Trying exact match for game: %s", game_name)
        # todo: use .search instead of .game
        game_exact = bgg_client.game(game_name, exact=True)
        if game_exact:
            log.info("Found exact match")
            game, _ = Game.get_or_create(
                game_name=game_exact.name,
                game_id=game_exact.id
            )
            return game
    except BGGItemNotFoundError:
        try:
            log.info("Failed to find exact match, trying fuzzy match")
            game_fuzzy = bgg_client.game(game_name, exact=False)
            if game_fuzzy:
                log.info("Found fuzzy match")
                game, _ = Game.get_or_create(
                    game_name=game_fuzzy.name,
                    game_id=game_fuzzy.id
                )
                return game
        except BGGItemNotFoundError:
            log.warning("Failed to get fuzzy match, no game name found")
            return
    return

def create_user_from_message(message: Message) -> User:
    """
    Reads a telegram message, extracts user info and returns a User ORM
    :param message:
    :return:
    """
    user, _ = User.get_or_create(
        telegram_userid=message.from_user.id
    )
    user.first_name = message.from_user.first_name
    user.last_name = message.from_user.last_name

    return user

def get_message_without_command(message: Message) -> str:
    """Extracts the message text by deleting the first word (usually a commmand)"""
    text = get_message_contents(message)
    return text.split(" ")[1]

def parse_message(message: Message) -> Tuple[Optional[Post], Optional[Game], Optional[User]]:
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
    bgg_client = BGGClient(cache=CacheBackendMemory(ttl=3600*24*7), access_token=os.getenv('BGG_BEARER'))
    game = get_game_details(game_name, bgg_client)
    if not game:
        log.warning("Game not found")
        return None, None, None

    post = Post(
        post_type=message_type,
        text=message_text,
        active=1,
        user=user,
        game=game
    )
    game.save()
    user.save()
    post.save()

    return post, game, user

def find_post_tag(message: Message) -> Optional[str]:
    """
    Finds the post tag from a message (eg: #sold, #found)
    """
    message_text = get_message_contents(message)
    tag = parse_tag(message_text)
    return tag


def is_post_tag_banned(post_tag:str, chat_type:str) -> bool:
    """
    True if a post tag is not allowed in its specific context (DM or group)
    """
    banned_in_dm = True if post_tag in TAGS_BANNED_IN_DM and chat_type=="private" else False
    banned_in_group = True if post_tag in TAGS_BANNED_IN_GROUP and chat_type!="private" else False
    return banned_in_dm or banned_in_group
