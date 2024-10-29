from peewee import *

db = SqliteDatabase('database/meeple-matchmaker.db')

class Game(Model):
    id = AutoField()
    game_name = TextField()
    game_id = IntegerField(unique=True)
    bgg_link = TextField(null=True)

    class Meta:
        database = db
        table_name = 'game'

# db.create_tables([Game])
# admin = Game(telegram_userid=1, telegram_username='sahil')
# admin.save()
#
# users = admin.select().execute()
# for i in users:
#     print('here', i.telegram_userid)