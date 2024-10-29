import peewee
from peewee import *
from user import User
import logging

logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

db = SqliteDatabase('database/meeple-matchmaker.db')

class Post(Model):
    post_type = TextField(null=False)
    game_id = IntegerField(null=False)
    text = TextField(null=False)
    user_name = TextField(null=False)
    active = BooleanField(null=False)
    game_name = TextField(null=False)

    class Meta:
        database = db
        table_name = 'post'
        primary_key = CompositeKey('post_type', 'game_id', 'text', 'user_name', 'active', 'game_name')
