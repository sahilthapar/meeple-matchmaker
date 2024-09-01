import pytest
import sqlite3
from src.database import init_post_db, read_post_db, write_to_post_db, disable_posts, read_user_posts
from src.telegrampost import parse_message


class TestDatabase:

    @pytest.fixture(name="post")
    def post(self, mocker):
        message = mocker.patch("telegram.Message")
        message.text = "#seekingInterest Terraforming Mars"
        message.from_user.id = 101
        message.from_user.first_name = "Jacob"
        return parse_message(message)

    @pytest.fixture(name="sample_data_tuple")
    def sample_data_tuple(self):
        return 'sale', 167791, '#seekinginterest terraforming mars', '101', 'Jacob', 1, 'Terraforming Mars'

    @pytest.fixture(name="sample_data_tuples")
    def sample_data_tuples(self):
        return [
            ('sale', 167791, '#seekinginterest terraforming mars', '101', 'Jacob', 1, 'Terraforming Mars'),
            ('search', 167791, '#lookingfor terraforming mars', '102', 'Henry', 1, 'Terraforming Mars'),
            ('sale', 321, '#selling ark nova', '101', 'Jacob', 1, 'Ark Nova'),
            ('sale', 999, '#selling destinies', '104', 'Marcus', 0, 'Destinies'),
            ('search', 123, '#lookingfor monopoly', '101', 'Jacob', 1, 'Monopoly'),
            ('search', 345, '#lookingfor wingspan', '103', 'Cristiano', 0, 'Wingspan'),
        ]

    @pytest.fixture(name="con")
    def con(self):
        return sqlite3.connect(":memory:")

    @pytest.fixture(name="cursor")
    def cursor(self, con):
        return con.cursor()

    def test_init_post_db(self, cursor):
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
            'INSERT INTO post (post_type, game_id, text, user_id, user_name, active) VALUES (?,?,?,?,?,?)',
            sample_data_tuples
        )
        con.commit()
        expected_data = [('102', 'Henry')]
        # by game id
        data = read_post_db(cursor, game_id=167791, post_type="search")
        assert list(data) == expected_data

    def test_read_post_db_by_type(self, con, cursor, post, sample_data_tuples):
        init_post_db(cursor)
        cursor.executemany(
            'INSERT INTO post (post_type, game_id, text, user_id, user_name, active) VALUES (?,?,?,?,?,?)',
            sample_data_tuples
        )
        con.commit()
        expected_data = [('101', 'Jacob')]
        # by game id
        data = read_post_db(cursor, game_id=167791, post_type="sale")
        assert list(data) == expected_data

    @pytest.mark.parametrize(
        argnames="post_type,game_id,expected_data",
        argvalues=[
            # disable_all
            (None, None, []),
            # disable terraforming sale for Jacob
            (
                'sale',
                167791,
                [
                    ('sale', 321, '#selling ark nova', '101', 'Jacob', 1),
                    ('search', 123, '#lookingfor monopoly', '101', 'Jacob', 1),
                ]
            ),
            # disable monopoly search for Jacob
            (
                'search',
                123,
                [
                    ('sale', 167791, '#seekinginterest terraforming mars', '101', 'Jacob', 1),
                    ('sale', 321, '#selling ark nova', '101', 'Jacob', 1),
                ]
            )
        ],
        ids=["disable_all", "disable_sold_tfm", "disable_found_monopoly"]
    )
    def test_disable_posts_all(self, con, cursor, post, sample_data_tuples, post_type, game_id, expected_data):
        init_post_db(cursor)
        cursor.executemany(
            'INSERT INTO post (post_type, game_id, text, user_id, user_name, active) VALUES (?,?,?,?,?,?)',
            sample_data_tuples
        )
        con.commit()
        # by game id
        disable_posts(cursor, user_id=101, post_type=post_type, game_id=game_id)
        data = cursor.execute("SELECT * FROM post WHERE user_id = 101 and active = 1")
        assert list(data) == expected_data

    @pytest.mark.parametrize(
        argnames="post_type, user_id, expected_data",
        argvalues=[
            (
                "sale",
                None,
                [
                    ('sale', 167791, '#seekinginterest terraforming mars', '101', 'Jacob'),
                    ('sale', 321, '#selling ark nova', '101', 'Jacob'),
                ]
            ),
            (
                "search",
                None,
                [
                    ('search', 167791, '#lookingfor terraforming mars', '102', 'Henry'),
                    ('search', 123, '#lookingfor monopoly', '101', 'Jacob'),
                ]
            ),
            (
                None,
                101,
                [
                    ('sale', 167791, '#seekinginterest terraforming mars', '101', 'Jacob'),
                    ('sale', 321, '#selling ark nova', '101', 'Jacob'),
                    ('search', 123, '#lookingfor monopoly', '101', 'Jacob'),
                ]
            ),
        ],
        ids=[
            "list_all_active_sales",
            "list_all_active_searches",
            "list_all_active_posts_for_user"
        ]
    )
    def test_read_user_posts(self, con, cursor, post, sample_data_tuples,
                             post_type, user_id, expected_data):
        init_post_db(cursor)
        cursor.executemany(
            'INSERT INTO post (post_type, game_id, text, user_id, user_name, active) VALUES (?,?,?,?,?,?)',
            sample_data_tuples
        )
        con.commit()
        data = read_user_posts(cursor, post_type=post_type, user_id=user_id)
        assert list(data) == expected_data




