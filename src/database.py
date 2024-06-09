from src.telegrampost import TelegramPost
import sqlite3
from typing import Optional
from sqlite3 import Cursor

def write_to_post_db(cursor: Cursor, posts: list[TelegramPost]):
    sql_tuples = [(
        post.post_type, post.game_id, post.text, post.user_id, post.user_name, 1
    ) for post in posts]
    cursor.executemany(
        'INSERT INTO post (post_type, game_id, text, user_id, user_name, active) VALUES (?,?,?,?,?,?)',
        sql_tuples
    )


def read_post_db(cursor: Cursor,
                 game_id: int,
                 post_type: str):
    filter_clause = f"""
        WHERE game_id = {str(game_id)}
        AND post_type = "{post_type}"
    """
    data = cursor.execute(f"SELECT DISTINCT user_id, user_name FROM post {filter_clause}").fetchall()
    return data


def init_post_db(cursor):
    sql = """
        CREATE TABLE post(
            post_type VARCHAR,
            game_id INTERGER,
            text VARCHAR,
            user_id VARCHAR,
            user_name VARCHAR,
            active BOOLEAN
        )
    """
    cursor.execute(sql)

#
# if __name__ == '__main__':
#     con = sqlite3.connect("meeple-matchmaker")
#     cur = con.cursor()
#     # init_post_db(cur)
#     rows = cur.execute("SELECT * FROM post")
#     for row in rows:
#         print(row)
