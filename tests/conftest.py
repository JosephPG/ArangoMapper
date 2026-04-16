from arango.database import StandardDatabase
from pytest import fixture

from app.database.conn import get_db

from tests.utils import restart_db


@fixture
def db():
    db: StandardDatabase = get_db()
    yield db
    restart_db(db)
