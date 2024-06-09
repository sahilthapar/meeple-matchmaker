from telegram import Message
from typing import Optional, Tuple
from logging import getLogger
from boardgamegeek import BGGClient, BGGItemNotFoundError
from boardgamegeek.objects.games import BoardGame


log = getLogger()


def get_game_id(game_name: str, bgg_client: BGGClient) -> Optional[BoardGame]:
    try:
        log.info("Trying exact match")
        game_exact = bgg_client.game(game_name, exact=True)
        if game_exact:
            return game_exact.id
    except BGGItemNotFoundError:
        log.info("Failed to find exact match")
        game_fuzzy = bgg_client.game(game_name, exact=False)
        return game_fuzzy.id

class TelegramPost:
    def __init__(self, text: str, user_id: int, user_name: str):
        self.text = text
        self.post_type = 'post'
        self.table_name = 'post'
        self.bgg_client = BGGClient()
        self.game_id = None
        self.user_id = user_id
        self.user_name = user_name
        self.insert_into_db = False

    def _get_game(self) -> Optional[BoardGame]:
        return get_game_id(self.text, self.bgg_client)

    def to_db_tuple(self):
        pass


class TelegramSearchPost(TelegramPost):
    def __init__(self, text: str, user_id: int, user_name: str):
        super().__init__(text, user_id, user_name)
        self.post_type = 'search'
        self.table_name = 'search'
        self.game_id = self._get_game()
        self.user_id = user_id
        self.user_name = user_name
        self.insert_into_db = True

    def to_db_tuple(self, active=True) -> Tuple:
        return self.post_type, self.game_id, self.text, self.user_id, self.user_name, active


class TelegramSalePost(TelegramPost):
    def __init__(self, text: str, user_id: int, user_name: str):
        super().__init__(text, user_id, user_name)
        self.post_type = 'sale'
        self.table_name = 'post'
        self.game_id = self._get_game()
        self.user_id = user_id
        self.user_name = user_name
        self.insert_into_db = True

    def to_db_tuple(self, active=True) -> Tuple:
        return self.post_type, self.game_id, self.text, self.user_id, self.user_name, active


class TelegramSoldPost(TelegramPost):
    def __init__(self, text: str, user_id: int, user_name: str):
        super().__init__(text, user_id, user_name)
        self.post_type = 'sold'
        self.table_name = 'post'
        self.game_id = self._get_game()
        self.user_id = user_id
        self.user_name = user_name
        self.insert_into_db = True

    def to_db_tuple(self, active=True) -> Tuple:
        return self.post_type, self.game_id, self.text, self.user_id, self.user_name, active


class TelegramFoundPost(TelegramPost):
    def __init__(self, text: str, user_id: int, user_name: str):
        super().__init__(text, user_id, user_name)
        self.post_type = 'found'
        self.table_name = 'post'
        self.game_id = self._get_game()
        self.user_id = user_id
        self.user_name = user_name
        self.insert_into_db = True

    def to_db_tuple(self, active=True) -> Tuple:
        return self.post_type, self.game_id, self.text, self.user_id, self.user_name, active


def get_post(message: Message) -> TelegramPost:
    msg = message.text.lower()
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    if '#lookingfor' in msg:
        text = msg.replace('#lookingfor', '').strip()
        return TelegramSearchPost(text, user_id, user_name)
    elif '#sale' in msg or '#selling' in msg or "#seekinginterest" in msg or '#sell' in msg:
        text = msg\
            .replace('#sale', '')\
            .replace('#selling', '')\
            .replace('#seekinginterest', '') \
            .replace('#sell', '') \
            .strip()
        return TelegramSalePost(text, user_id, user_name)
    elif '#sold' in msg:
        text = msg\
            .replace('#sold', '')\
            .strip()
        return TelegramSoldPost(text, user_id, user_name)
    elif '#found' in msg:
        text = msg\
            .replace('#found', '')\
            .strip()
        return TelegramFoundPost(text, user_id, user_name)
    return TelegramPost(msg, user_id, user_name)
