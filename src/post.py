from typing import Optional
from logging import getLogger
from boardgamegeek import BGGClient, BGGItemNotFoundError
from boardgamegeek.objects.games import BoardGame


log = getLogger()


class Post:
    def __init__(self, contents: str):
        self.contents = contents
        self.post_type = 'post'
        self.table_name = 'post'
        self.bgg_client = BGGClient()
        self.game = None

    def get_game(self) -> Optional[BoardGame]:
        try:
            log.info("Trying exact match")
            game_exact = self.bgg_client.game(self.contents, exact=True)
            if game_exact:
                return game_exact
        except BGGItemNotFoundError:
            log.info("Failed to find exact match")
            game_fuzzy = self.bgg_client.game(self.contents, exact=False)
            return game_fuzzy


class SearchPost(Post):
    def __init__(self, contents: str):
        super().__init__(contents)
        self.post_type = 'search'
        self.table_name = 'search'
        self.game = self.get_game()
        self.user = 'test'

class InterestPost(Post):
    def __init__(self, contents: str):
        super().__init__(contents)
        self.post_type = 'interest'
        self.table_name = 'interest'
        self.game = self.get_game()
        self.user = 'test'


class SalePost(Post):
    def __init__(self, contents: str):
        super().__init__(contents)
        self.post_type = 'sale'
        self.table_name = 'sale'
        self.game = self.get_game()
        self.user = 'test'


def get_post(message: str) -> Post:
    message = message.lower()

    if '#lookingfor' in message:
        contents = message.replace('#lookingfor', '').strip()
        return SearchPost(contents)
    elif '#seekinginterest' in message:
        contents = message.replace('#seekinginterest', '').strip()
        return InterestPost(contents)
    elif '#sale' in message or '#selling' in message:
        contents = message.replace('#sale', '').replace('#selling', '').strip()
        return SalePost(contents)
    return Post(message)

