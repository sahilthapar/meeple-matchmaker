import pytest
import sqlite3
from src.database import init_post_db, read_post_db, write_to_post_db
from src.telegrampost import get_post


class TestDatabase:

    @pytest.fixture(name="post")
    def post(self):
        return get_post("#seekingInterest Terraforming Mars")

    @pytest.fixture(name="sample_data_tuple")
    def sample_data_tuple(self):
        return 'interest', 167791, 'terraforming mars', 'test', 1

    @pytest.fixture(name="sample_data_tuples")
    def sample_data_tuples(self):
        return [
            ('interest', 167791, 'terraforming mars', 'test', 1),
            ('search', 167791, 'terraforming mars', 'test-one', 1),
            ('sale', 167791, 'terraforming mars', 'test-two', 1),
            ('search', 123, 'monopoly', 'test-two', 1),
        ]

    @pytest.fixture(name="con")
    def con(self):
        return sqlite3.connect(":memory:")

    @pytest.fixture(name="cursor")
    def cursor(self, con):
        return con.cursor()

    def test_post_db_init(self, cursor):
        init_post_db(cursor)
        data = cursor.execute("SELECT sql FROM sqlite_schema WHERE NAME = 'post'")
        assert len(list(data)) == 1

    def test_write_to_post_db(self, con, cursor, post, sample_data_tuple):
        init_post_db(cursor)

        write_to_post_db(cursor, [post])
        con.commit()

        data = cursor.execute("SELECT * FROM post")
        assert list(data) == [sample_data_tuple]

    def test_read_post_db_by_id(self, con, cursor, post, sample_data_tuples):
        init_post_db(cursor)
        cursor.executemany(
            'INSERT INTO post (post_type, game_id, contents, user, active) VALUES (?,?,?,?,?)',
            sample_data_tuples
        )
        con.commit()

        # by game id
        data = read_post_db(cursor, game_id=[167791, 321])
        assert list(data) == list(filter(lambda x: x[1] in [167791], sample_data_tuples))

    def test_read_post_db_by_type(self, con, cursor, post, sample_data_tuples):
        init_post_db(cursor)
        cursor.executemany(
            'INSERT INTO post (post_type, game_id, contents, user, active) VALUES (?,?,?,?,?)',
            sample_data_tuples
        )
        con.commit()

        # by game id
        data = read_post_db(cursor, post_type="search")
        assert list(data) == list(filter(lambda x: x[0] == "search", sample_data_tuples))


