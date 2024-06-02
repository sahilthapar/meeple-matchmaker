from typing import Optional
from logging import getLogger
from boardgamegeek import BGGClient, BGGItemNotFoundError
from boardgamegeek.objects.games import BoardGame


log = getLogger()


class Post:
    def __init__(self, contents: str, client: BGGClient):
        self.contents = contents
        self.post_type = 'post'
        self.table_name = 'post'
        self.bgg_client = client
        self.game = self.get_game()
        self.user = self.get_user()

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


    def get_user(self):
        pass


class SearchPost(Post):
    def __init__(self, contents: str, bgg_client: BGGClient):
        super().__init__(contents, bgg_client)
        self.post_type = 'search'
        self.table_name = 'search'

class InterestPost(Post):
    def __init__(self, contents: str, bgg_client: BGGClient):
        super().__init__(contents, bgg_client)
        self.post_type = 'interest'
        self.table_name = 'interest'


class SalePost(Post):
    def __init__(self, contents: str, bgg_client: BGGClient):
        super().__init__(contents, bgg_client)
        self.post_type = 'sale'
        self.table_name = 'sale'


def get_post(message: str, bgg_client: BGGClient) -> Post:
    message = message.lower()

    if '#lookingfor' in message:
        contents = message.replace('#lookingfor', '').strip()
        return SearchPost(contents, bgg_client)
    elif '#seekinginterest' in message:
        contents = message.replace('#seekinginterest', '').strip()
        return InterestPost(contents, bgg_client)
    elif '#sale' in message or '#selling' in message:
        contents = message.replace('#sale', '').replace('#selling', '').strip()
        return SalePost(contents, bgg_client)
    return Post(message, bgg_client)

