# This script is used to migrate the legacy meeple_matchmaker.db::posts table to user_post


# Step 1: Create a temporary LegacyPost model
from peewee import Model, SqliteDatabase, TextField, IntegerField, BooleanField, CompositeKey
from src.models import Post, Game, User, db
from playhouse.shortcuts import model_to_dict

db.init("database/meeple-matchmaker.db")

class LegacyPost(Model):
    post_type = TextField()
    game_id = IntegerField()
    text = TextField()
    user_id = TextField()
    user_name = TextField()
    active = BooleanField()
    game_name = TextField(null=True)

    class Meta:
        database = db
        table_name = 'post'
        primary_key = CompositeKey('post_type', 'game_id', 'text', 'user_id', 'user_name', 'active', 'game_name')


# Step 2: Read all data from LegacyPost
data = LegacyPost.select().execute()
print(len(data))

db.create_tables([Post])

# Step 3: Create instances of new models, User, Game, Post and save them
for lp in data:
    print(model_to_dict(lp))
    game, _ = Game.get_or_create(game_id=lp.game_id)
    game.game_name = lp.game_name
    print('Migrating Game: ', game.game_name)
    game.save()

    user, _ = User.get_or_create(telegram_userid=lp.user_id)
    user.first_name = lp.user_name
    print('Migrating User: ', user.first_name)
    user.save()

    post = Post(
        post_type=lp.post_type,
        text=lp.text,
        active=bool(lp.active),
        user=user,
        game=game
    )
    print('Saving post: ', post.text)
    post.save()

# Step 5: Validate data