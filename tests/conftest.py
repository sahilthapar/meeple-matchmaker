"""Module for intialising the database and other possible test configurations"""
import pytest
from src.models import db, User, Game, Post

@pytest.fixture(name="database")
def database():
    """Initialises the model sqlite db as an in memory instance"""
    db.init(":memory:")
    return db

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

    gameArray = [
        MockGame("Monopoly",1406),
        MockGame("Lost Ruins of Arnak",312484),
        MockGame("The Guild of Merchant Explorers",350933),
        MockGame("Terraforming Mars",167791)
        ]
    def game(self, game_name:str, exact:bool):
        for game in self.gameArray:
            if game_name.lower() in game.name.lower():
                return game
        return None

