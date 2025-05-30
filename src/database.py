from typing import Optional, Iterable, Union

from peewee import SqliteDatabase
from src.models import Post, User, Game
from functools import reduce
import operator


def init_tables(db: SqliteDatabase) -> None:
    db.create_tables([Post, User, Game])

def read_posts(
        user_id: Optional[int] = None,
        post_type: Optional[str] = None,
        game_id: Optional[Union[int, list[int]]] = None,
        is_active: Optional[bool] = True
) -> Iterable[Post]:

    clauses = [(Post.active == is_active)]

    if user_id:
        user = User.get(telegram_userid=user_id)
        clauses.append((Post.user == user))
    if post_type:
        clauses.append((Post.post_type == post_type))
    if game_id:
        # change to a sub-query
        if isinstance(game_id, int):
            game_id = [game_id]
        games = Game.select().where(Game.game_id << game_id)

        clauses.append((Post.game.in_(games)))

    data = Post\
        .select(Post.post_type, Post.user, Post.game, Post.active, Game.game_id, Game.game_name, User.first_name, User.telegram_userid)\
        .join(Game, on=(Post.game == Game.id))\
        .join(User, on=(Post.user == User.id)) \
        .where(reduce(operator.and_, clauses)) \
        .order_by(Post.post_type, Game.game_name, User.first_name) \
        .distinct()
    return data.execute()


def disable_posts(user_id: int, post_type: Optional[str] = None, game_id: Optional[int] = None) -> None:
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
