from src.game import Game, get_game
from src.user import User, get_user


class Post:
    def __init__(self, game: Game, user: User):
        self.game = game
        self.user = user
        self.post_type = 'Post'


class SearchPost(Post):
    def __init__(self, game: Game, user: User):
        super().__init__(game, user)
        self.post_type = 'Search'

class InterestPost(Post):
    def __init__(self, game: Game, user: User):
        super().__init__(game, user)
        self.post_type = 'Interest'


class SalePost(Post):
    def __init__(self, game: Game, user: User):
        super().__init__(game, user)
        self.post_type = 'Sale'


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

