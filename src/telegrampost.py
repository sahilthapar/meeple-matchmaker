from telegram import Message
from typing import Optional, Tuple
from logging import getLogger
from boardgamegeek import BGGClient, BGGItemNotFoundError
from boardgamegeek.objects.games import BoardGame
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
}

def parse_tag(message: str) -> str:
    tag = re.search(
        pattern="^#lookingfor|^#sale|^#selling|^#seekinginterest|^#sell|^#sold|^#found",
        string=message
    )
    if not tag:
        return ""
    return tag.group()

def parse_game_name(message: str) -> str:
    first_line = message.strip().split("\n")[0]
    return first_line


def get_game_id(game_name: str, bgg_client: BGGClient) -> Optional[BoardGame]:
    try:
        log.info("Trying exact match")
        game_exact = bgg_client.game(game_name, exact=True)
        if game_exact:
            return game_exact.id
    except BGGItemNotFoundError:
        try:
            log.info("Failed to find exact match")
            game_fuzzy = bgg_client.game(game_name, exact=False)
            return game_fuzzy.id
        except BGGItemNotFoundError:
            log.warning("Failed to get fuzzy match, no game name found")
            return None


def parse_message(message: Message) -> Optional[SimpleNamespace]:
    raw_text = message.text.lower()
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    tag = parse_tag(raw_text)
    message_without_tag = raw_text.replace(tag, "").strip()
    message_type = TYPE_LOOKUP.get(tag, None)
    if not message_type:
        return None
    game_name = parse_game_name(message_without_tag)
    bgg_client = BGGClient()
    game_id = get_game_id(game_name, bgg_client)

    return SimpleNamespace(
        post_type=message_type,
        text=raw_text,
        game_id=game_id,
        user_id=user_id,
        user_name=user_name,
        to_db_tuple=(message_type, game_id, raw_text, user_id, user_name, 1)
    )

