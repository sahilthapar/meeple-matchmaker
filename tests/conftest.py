import pytest
from src.models import db

@pytest.fixture(name="database")
def database():
    db.init(":memory:")
    return db 