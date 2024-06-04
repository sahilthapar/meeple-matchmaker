from telegram import Message
from typing import Optional, Tuple
from logging import getLogger
from boardgamegeek import BGGClient, BGGItemNotFoundError
from boardgamegeek.objects.games import BoardGame


log = getLogger()


class TelegramPost:
    def __init__(self, text: str):
        self.text = text
        self.post_type = 'post'
        self.table_name = 'post'
        self.bgg_client = BGGClient()
        self.game = None
        self.user = None
        self.insert_into_db = False

    def _get_game(self) -> Optional[BoardGame]:
        try:
            log.info("Trying exact match")
            game_exact = self.bgg_client.game(self.text, exact=True)
            if game_exact:
                return game_exact
        except BGGItemNotFoundError:
            log.info("Failed to find exact match")
            game_fuzzy = self.bgg_client.game(self.text, exact=False)
            return game_fuzzy

    def to_db_tuple(self):
        pass


class TelegramSearchPost(TelegramPost):
    def __init__(self, text: str):
        super().__init__(text)
        self.post_type = 'search'
        self.table_name = 'search'
        self.game = self._get_game()
        self.user = 'test'
        self.insert_into_db = True

    def to_db_tuple(self, active=True) -> Tuple:
        return self.post_type, self.game.id, self.text, self.user, active

# class InterestPost(Post):
#     def __init__(self, contents: str):
#         super().__init__(contents)
#         self.post_type = 'interest'
#         self.table_name = 'interest'
#         self.game = self._get_game()
#         self.user = 'test'


class TelegramSalePost(TelegramPost):
    def __init__(self, text: str):
        super().__init__(text)
        self.post_type = 'sale'
        self.table_name = 'sale'
        self.game = self._get_game()
        self.user = 'test'
        self.insert_into_db = True

    def to_db_tuple(self, active=True) -> Tuple:
        return self.post_type, self.game.id, self.text, self.user, active


def get_post(message: Message) -> TelegramPost:
    message = message.text.lower()
    print(message)
    if '#lookingfor' in message:
        text = message.replace('#lookingfor', '').strip()
        return TelegramSearchPost(text)
    # elif '#seekinginterest' in message:
    #     text = message.replace('#seekinginterest', '').strip()
    #     return InterestPost(text)
    elif '#sale' in message or '#selling' in message or "#seekinginterest" in message:
        text = message\
            .replace('#sale', '')\
            .replace('#selling', '')\
            .replace('#seekinginterest', '')\
            .strip()
        return TelegramSalePost(text)
    return TelegramPost(message)

