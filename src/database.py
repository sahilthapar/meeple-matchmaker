from src.telegrampost import TelegramPost
import sqlite3
from typing import Optional
from sqlite3 import Cursor

def write_to_post_db(cursor: Cursor, posts: list[TelegramPost]):
    sql_tuples = [(
        post.post_type, post.game_id.id, post.text, post.user_id, True
    ) for post in posts]
    cursor.executemany(
        'INSERT INTO post (post_type, game_id, contents, user, active) VALUES (?,?,?,?,?)',
        sql_tuples
    )


def read_post_db(cur, game_id: Optional[list[int]] = None, post_type: Optional[str] = None):
    filter_clause = ""
    filter_game_clause = ""
    filter_post_type_clause = ""

    if game_id:
        str_filter_game_id = [str(x) for x in game_id]
        filter_game_clause = f"game_id IN ({', '.join(str_filter_game_id)})"

    if post_type:
        filter_post_type_clause = f"post_type = '{post_type}'"

    if filter_game_clause and filter_post_type_clause:
        filter_clause = f"WHERE {filter_game_clause} AND {filter_post_type_clause}"
    elif filter_game_clause:
        filter_clause = f"WHERE {filter_game_clause}"
    elif filter_post_type_clause:
        filter_clause = f"WHERE {filter_post_type_clause}"

    data = cur.execute(f"SELECT * FROM post {filter_clause}").fetchall()
    return data


def init_post_db(cursor):
    sql = """
        CREATE TABLE post(
            post_type VARCHAR,
            game_id INTERGER,
            contents VARCHAR,
            user VARCHAR,
            active BOOLEAN
        )
    """
    cursor.execute(sql)


if __name__ == '__main__':
    con = sqlite3.connect("meeple-market-bot")
    cur = con.cursor()