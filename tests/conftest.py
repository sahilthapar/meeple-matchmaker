"""Module for intialising the database and other possible test configurations"""
import asyncio
import pytest
from src.models import db, User, Game, Post, UserCollection
from tests.helpers import MockBGGClient

@pytest.fixture(name="database")
def database():
    """Initialises the model sqlite db as an in memory instance"""
    db.init(":memory:")
    db.connect(reuse_if_open=True)
    db.create_tables([User, Game, Post, UserCollection])
    yield db
    db.drop_tables([User, Game, Post, UserCollection])
    db.close()

@pytest.fixture(name="bgg_client")
def bgg_client():
    """Fixture that can be used to replace bgg_client with a mock eventually"""
    return MockBGGClient()

@pytest.fixture(name="mock_update")
def mock_update(mocker):
    """Fixture thats used to mock a telegram update entity"""
    update = mocker.patch("telegram.Update")

    # Get or create event loop for creating futures
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    f = asyncio.Future()
    f.set_result('text')
    update.message.reply_text.return_value = f
    update.message.set_reaction.return_value = f

    return update