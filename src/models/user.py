from peewee import *

db = SqliteDatabase('database/meeple-matchmaker.db')

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

# db.create_tables([User])
# admin = User(telegram_userid=1, telegram_username='sahil')
# admin.save()
#
# users = admin.select().execute()
# for i in users:
#     print('here', i.telegram_userid)