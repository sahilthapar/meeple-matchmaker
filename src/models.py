from peewee import SqliteDatabase, Model
from peewee import AutoField, IntegerField, TextField, BooleanField, ForeignKeyField

db = SqliteDatabase(None)

class User(Model):
    id = AutoField()
    telegram_userid = IntegerField(unique=True)
    first_name = TextField(null=True)
    last_name = TextField(null=True)
    discord_handle = TextField(null=True, unique=True)
    bgg_username = TextField(null=True, unique=True)

    class Meta:
        database = db
        table_name = 'user'

class Game(Model):
    id = AutoField()
    game_name = TextField(null=True)
    game_id = IntegerField(unique=True)
    bgg_link = TextField(null=True)

    class Meta:
        database = db
        table_name = 'game'

class Post(Model):
    id = AutoField()
    post_type = TextField()
    text = TextField()
    active = BooleanField(default=True)
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)

    class Meta:
        database = db
        table_name = 'user_post'
#
# db.init('database/meeple-matchmaker.db')
# db.create_tables([User, Game, Post])
#
#
# user, _ = User.get_or_create(telegram_userid=1)
# print('user', user)
# user.update(bgg_username='it', discord_handle='worked').execute()
#
# game, _ = Game.get_or_create(game_id=1406)
# print('game', game)
# game.update(game_name='Monopoly').execute()
#
#
# post = Post(post_type="search", text="#lookingfor monopoly", active=1,user=user, game=game)
# post.save()
# print('post', post)
#
# posts = post.select().execute()
# for i in posts:
#     print('here', i.post_type, i.text, i.user.discord_handle, i.game.game_id, i.game.game_name)