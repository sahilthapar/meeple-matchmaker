from src.thing import Thing

class Game(Thing):
    def __init__(self, name):
        super().__init__(name)


def get_game(message: str) -> Game:
    pass