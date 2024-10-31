from telegram import Message
from typing import Optional, Tuple
from logging import getLogger
from boardgamegeek import BGGClient, BGGItemNotFoundError, CacheBackendMemory  # type: ignore
import re

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

def get_message_contents(message: Message) -> str:
    text = message.text or message.caption
    return text.lower() if text else ""

def parse_tag(message: str) -> str:
    tag = re.search(
        pattern="^#lookingfor|^#iso|^#looking|^#sale|^#selling|^#seekinginterest|^#sell|^#auction|^#sold|^#found",
        string=message
    )
    if not tag:
        return ""
    return tag.group()

def parse_game_name(message: str) -> str:
    first_line = message.strip().split("\n")[0]
    return first_line.replace("game name:", "").replace("game:", "").strip()

def get_game_details(game_name: str, bgg_client: BGGClient) -> Optional[Game]:
    try:
        log.info(f"Trying exact match for game: {game_name}")
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
    bgg_client = BGGClient(cache=CacheBackendMemory(ttl=3600*24*7))
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

