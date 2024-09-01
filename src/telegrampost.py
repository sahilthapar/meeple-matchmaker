from telegram import Message
from typing import Optional
from logging import getLogger
from boardgamegeek import BGGClient, BGGItemNotFoundError, CacheBackendMemory  # type: ignore
from boardgamegeek.objects.games import BoardGame  # type: ignore
from types import SimpleNamespace
import re


log = getLogger()


TYPE_LOOKUP = {
    "#lookingfor": "search",
    "#sale": "sale",
    "#selling": "sale",
    "#seekinginterest": "sale",
    "#sell": "sale",
    "#sold": "sold",
    "#found": "found",
    "#iso": "search",
    "#looking": "search",
    "#auction": "sale",
}

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
    return first_line

def get_game(game_name: str, bgg_client: BGGClient) -> Optional[BoardGame]:
    try:
        log.info("Trying exact match")
        game_exact = bgg_client.game(game_name, exact=True)
        if game_exact:
            return game_exact
    except BGGItemNotFoundError:
        try:
            log.info("Failed to find exact match, trying fuzzy match")
            game_fuzzy = bgg_client.game(game_name, exact=False)
            return game_fuzzy
        except BGGItemNotFoundError:
            log.warning("Failed to get fuzzy match, no game name found")
            return None
    return None

def parse_message(message: Message) -> Optional[SimpleNamespace]:
    raw_text = message.text.lower() if message.text else ""
    user_id = message.from_user.id if message.from_user else None
    user_name = message.from_user.first_name if message.from_user else None

    tag = parse_tag(raw_text)
    message_without_tag = raw_text.replace(tag, "").strip()
    message_type = TYPE_LOOKUP.get(tag, None)
    if not message_type:
        return None
    game_name = parse_game_name(message_without_tag)
    bgg_client = BGGClient(cache=CacheBackendMemory(ttl=3600*24*7))
    game = get_game(game_name, bgg_client)
    if not game:
        log.warning("Game not found")
        return None
    return SimpleNamespace(
        post_type=message_type,
        text=raw_text,
        game_id=game.id,
        user_id=user_id,
        user_name=user_name,
        game_name=game.name,
        to_db_tuple=(message_type, game.id, raw_text, user_id, user_name, 1, game_name)
    )

