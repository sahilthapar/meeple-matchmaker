
from boardgamegeek import BGGItemNotFoundError
from src.models import  User, Game, Post
def initialize_post(
            post_type: str, text: str, 
            active: bool,
            user_id: int, 
            user_name: str,
            game_id: int, 
            game_name: str
    ):
    """Fixture that initialises a specific post for a user-game-post_type set"""
    user, _ = User.get_or_create(telegram_userid=user_id, first_name=user_name)
    game, _ = Game.get_or_create(game_id=game_id, game_name=game_name)

    user.save()
    game.save()
    post = Post(post_type=post_type, text=text, active=active, user=user, game=game)
    post.save()
    return post


class MockBGGClient:
    class MockGame:
        def __init__(self,name,game_id):
            self.name=name
            self.id=game_id

    game_array = [
        MockGame("Monopoly",1406),
        MockGame("Lost Ruins of Arnak",312484),
        MockGame("The Guild of Merchant Explorers",350933),
        MockGame("Terraforming Mars",167791)
        ]
    def game(self, game_name:str="", exact:bool=True, game_id:int=None):
        """
        Exact=True matches the name (case-insensitive)
        Exact=False is a strict check for Moopoly and returns Monopoly
        """
        if game_id:
            return [game for game in self.game_array if game.id==game_id][0]
        
        if exact:
            for game in self.game_array:
                if game_name.lower() in game.name.lower():
                    return game
        elif game_name=="Moopoly":
            return self.game_array[0]
        raise BGGItemNotFoundError
