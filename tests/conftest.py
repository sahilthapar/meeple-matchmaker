"""Module for intialising the database and other possible test configurations"""
import pytest
from src.models import db

@pytest.fixture(name="database")
def database():
    """Initialises the model sqlite db as an in memory instance"""
    db.init(":memory:")
    return db
