import pytest
from src.database import init_tables, read_post_db, disable_posts, read_user_posts
from src.models import User, Game, Post, db


class TestDatabase:

    @staticmethod
    def _post_model_to_tuple(post: Post):
        return post.post_type, post.game.game_id, post.user.first_name, post.active, post.game.game_name

    @pytest.fixture(name="database")
    def database(self):
        db.init(":memory:")
        return db

    @pytest.fixture(name="sample_posts")
    def sample_posts(self, database):
        init_tables(database)
        jacob = User(telegram_userid=101, first_name='Jacob')
        henry = User(telegram_userid=102, first_name='Henry')
        marcus = User(telegram_userid=103, first_name='Marcus')
        cristiano = User(telegram_userid=107, first_name='Cristiano')
        for user in [jacob, henry, marcus, cristiano]:
            user.save()

        tfm = Game(game_id=167791, game_name='Terraforming Mars')
        ark_nova = Game(game_id=321, game_name='Ark Nova')
        destinies = Game(game_id=999, game_name='Destinies')
        monopoly = Game(game_id=123, game_name='Monopoly')
        wingspan = Game(game_id=345, game_name='Wingspan')

        for game in [tfm, ark_nova, destinies, monopoly, wingspan]:
            game.save()

        Post(post_type='sale', text='#seekinginterest terraforming mars', active=True, user=jacob, game=tfm).save()
        Post(post_type='search', text='#lookingfor terraforming mars', active=True, user=henry, game=tfm).save()
        Post(post_type='sale', text='#selling ark nova', active=True, user=jacob, game=ark_nova).save()
        Post(post_type='sale', text='#selling destinies', active=False, user=marcus, game=destinies).save()
        Post(post_type='search', text='#lookingfor monopoly', active=True, user=jacob, game=monopoly).save()
        Post(post_type='search', text='#lookingfor wingspan', active=False, user=cristiano, game=wingspan).save()

    def test_init_tables(self, database):
        init_tables(database)
        data = database.get_tables()

        assert data == ['game', 'user', 'user_post']

    # def test_write_to_post_db(self, ):
    #     # create a new post
    #     # write it to db
    #     # check if it's written
    #     init_tables(cursor)
    #
    #     write_to_post_db(cursor, [post])
    #     con.commit()
    #
    #     data = cursor.execute("SELECT * FROM post")
    #     assert list(data) == [sample_data_tuple]

    @pytest.mark.parametrize(
        argnames='game_id,post_type,expected_data',
        argvalues=[
            (167791, 'search', [(102, 'Henry')]),
            (167791, 'sale', [(101, 'Jacob')]),

        ],
        ids=["search_tfm", "sale_tfm",]
    )
    def test_read_post_db(self, sample_posts, game_id, post_type, expected_data):
        data = read_post_db(game_id=game_id, post_type=post_type)

        user_data = [(d.user.telegram_userid, d.user.first_name) for d in data]

        assert user_data == expected_data

    @pytest.mark.parametrize(
        argnames="post_type,game_id,expected_inactives",
        argvalues=[
            # disable_all
            (
                    None,
                    None,
                    [
                        ('sale', 167791, 'Jacob', False, 'Terraforming Mars'),
                        ('sale', 321, 'Jacob', False, 'Ark Nova'),
                        ('search', 123, 'Jacob', False, 'Monopoly')
                    ]
            ),
            # disable terraforming sale for Jacob
            (
                    'sale',
                    167791,

                    [
                        ('sale', 167791, 'Jacob', False, 'Terraforming Mars'),
                    ]
            ),
            # disable monopoly search for Jacob
            (
                    'search',
                    123,
                    [
                        ('search', 123, 'Jacob', False, 'Monopoly')
                    ]
            )
        ],
        ids=["disable_all", "disable_sold_tfm", "disable_found_monopoly"]
    )
    def test_disable_posts_all(self, sample_posts, post_type, game_id, expected_inactives):
        jacob = User.get(telegram_userid=101)

        disable_posts(user_id=jacob.telegram_userid, post_type=post_type, game_id=game_id)

        jacobs_inactive_posts = Post.select().where((Post.active == False) & (Post.user == jacob)).execute()
        actual_inactives = [
            self._post_model_to_tuple(post) for post in jacobs_inactive_posts
        ]

        assert actual_inactives == expected_inactives

    @pytest.mark.parametrize(
        argnames="post_type, user_id, expected_data",
        argvalues=[
            (
                    "sale",
                    None,
                    [
                        ('sale', 321, 'Jacob', True, 'Ark Nova'),
                        ('sale', 167791, 'Jacob', True, 'Terraforming Mars'),
                    ]
            ),
            (
                    "search",
                    None,
                    [
                        ('search', 123, 'Jacob', True, "Monopoly"),
                        ('search', 167791, 'Henry', True, "Terraforming Mars"),
                    ]
            ),
            (
                    None,
                    101,
                    [
                        ('sale', 321, 'Jacob', True, "Ark Nova"),
                        ('sale', 167791, 'Jacob', True, "Terraforming Mars"),
                        ('search', 123, 'Jacob', True, "Monopoly"),
                    ]
            ),
        ],
        ids=[
            "list_all_active_sales",
            "list_all_active_searches",
            "list_all_active_posts_for_user"
        ]
    )
    def test_read_user_posts(self, sample_posts, post_type, user_id, expected_data):

        posts = read_user_posts(post_type=post_type, user_id=user_id)
        posts = [self._post_model_to_tuple(post) for post in posts]
        assert posts == expected_data
