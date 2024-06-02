from src.game import Game, get_game
from src.user import User, get_user


class Post:
    def __init__(self, game: str, user: str):
        self.game = game
        self.user = user
        self.post_type = 'post'
        self.table_name = 'post'


class SearchPost(Post):
    def __init__(self, game: str, user: str):
        super().__init__(game, user)
        self.post_type = 'search'
        self.table_name = 'search'

class InterestPost(Post):
    def __init__(self, game: str, user: str):
        super().__init__(game, user)
        self.post_type = 'interest'
        self.table_name = 'interest'


class SalePost(Post):
    def __init__(self, game: str, user: str):
        super().__init__(game, user)
        self.post_type = 'sale'
        self.table_name = 'sale'


def get_post(message: str) -> Post:
    game = get_game(message)
    user = get_user(message)
    message = message.lower()

    if 'lookingfor' in message:
        return SearchPost(game, user)
    elif 'seekinginterest' in message:
        return InterestPost(game, user)
    elif 'sale' in message or 'selling' in message:
        return SalePost(game, user)
    return Post(game, user)

