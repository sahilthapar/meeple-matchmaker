from typing import Optional, Tuple, Iterable

from peewee import SqliteDatabase
from src.models import Post, User, Game
from functools import reduce
import operator


def init_tables(db: SqliteDatabase) -> None:
    db.create_tables([Post, User, Game])

def read_posts(
        user_id: Optional[int],
        post_type: Optional[str],
        game_id: Optional[int],
        is_active: Optional[bool] = True
) -> Iterable[Post]:

    clauses = [(Post.active == is_active)]

    if user_id:
        user = User.get(telegram_userid=user_id)
        clauses.append((Post.user == user))
    if post_type:
        clauses.append((Post.post_type == post_type))
    if game_id:
        game = Game.get(game_id=game_id)
        clauses.append((Post.game == game))

    data = Post.select()\
        .where(reduce(operator.and_, clauses))\
        .order_by(Post.post_type, -Post.game, Post.user)\
        .execute()
    return data


def disable_posts(user_id: int, post_type: Optional[str], game_id: Optional[int]) -> None:
    user = User.get(telegram_userid=user_id)

    clauses = [
        (Post.user == user)
    ]

    if game_id:
        game = Game.get(game_id=game_id)
        clauses.append((Post.game == game))

    if post_type:
        clauses.append((Post.post_type == post_type))

    Post.update(active=False).where(reduce(operator.and_, clauses)).execute()

def update_game_name(cursor, game_id: int, game_name: str) -> None:
    sql = """
    UPDATE post SET game_name = :game_name
    WHERE game_id = :game_id
    """
    cursor.execute(sql, {"game_name": f'{game_name}', "game_id": game_id})
