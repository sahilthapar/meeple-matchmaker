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
