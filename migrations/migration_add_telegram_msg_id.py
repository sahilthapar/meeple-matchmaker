"""
Migration file to add a new telegram_msg_id column to the user_post table
Needs to be run from within the same folder as the db
"""
import sys

from playhouse.migrate import migrate, SchemaMigrator
from peewee import BigIntegerField, SqliteDatabase

db = SqliteDatabase("../database/meeple-matchmaker.db")
if "user_post" in db.get_tables():
    if "telegram_msg_id" in [col.name for col in db.get_columns("user_post")]:
        print("telegram_msg_id column already present in user_post table")
        sys.exit()

migrator = SchemaMigrator.from_database(db)

telegram_msg_id = BigIntegerField(null=True)

with db.atomic():
    migrate(
        migrator.add_column('user_post', 'telegram_msg_id', telegram_msg_id)
    )

print("MIGRATION COMPLETE: telegram_msg_id column added successfully")
