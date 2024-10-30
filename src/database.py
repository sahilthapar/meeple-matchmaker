from typing import Optional, Tuple, Iterable

from peewee import SqliteDatabase
from src.models import Post, User, Game
from functools import reduce
import operator


def read_user_posts(user_id: int, post_type: str) -> Iterable[Post]:

    clauses = [(Post.active == True)]

    if user_id:
        user = User.get(telegram_userid=user_id)
        clauses.append((Post.user == user))
    if post_type:
        clauses.append((Post.post_type == post_type))

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


def init_tables(db: SqliteDatabase) -> None:
    db.create_tables([Post, User, Game])

def read_post_db(game_id: int,
                 post_type: str) -> list[Tuple]:

    game = Game.get(game_id=game_id)
    data = Post\
        .select()\
        .where(
            (Post.post_type == post_type) &
            (Post.game == game) &
            (Post.active == True)
        )\
        .execute()
    return data

# def write_to_post_db(db: SqliteDatabase, posts: list[Post]):
#     sql_tuples = [(
#         post.post_type, post.game_id, post.text, post.user_id, post.user_name, 1, post.game_name
#     ) for post in posts]
#     cursor.executemany(
#         'INSERT INTO post (post_type, game_id, text, user_id, user_name, active, game_name) VALUES (?,?,?,?,?,?,?)',
#         sql_tuples
#     )
