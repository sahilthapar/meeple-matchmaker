from peewee import SqliteDatabase, Model
from peewee import AutoField, IntegerField, TextField, BooleanField, ForeignKeyField, DateTimeField
import datetime

db = SqliteDatabase(None)

class User(Model):
    """
    Represents a User
    """
    id = AutoField()
    telegram_userid = IntegerField(unique=True)
    first_name = TextField(null=True)
    last_name = TextField(null=True)
    discord_handle = TextField(null=True, unique=True)
    bgg_username = TextField(null=True, unique=True)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        database = db
        table_name = 'user'

class Game(Model):
    """
    Represents a BGG Game
    """
    id = AutoField()
    game_name = TextField(null=True)
    game_id = IntegerField(unique=True)
    bgg_link = TextField(null=True)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        database = db
        table_name = 'game'

class Post(Model):
    """
    Represents a telegram message (post)
    Parsed info contains
    - game info
    - user info
    - active status
    """
    id = AutoField()
    post_type = TextField()
    text = TextField()
    active = BooleanField(default=True)
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        database = db
        table_name = 'user_post'

class UserCollection(Model):
    """
    Represents a User's collection of games
    """
    id = AutoField()
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)
    status = TextField()
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        database = db
        table_name = 'user_collection'
