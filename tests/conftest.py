import pytest_asyncio
from arango.database import StandardDatabase
from arangoasync.database import StandardDatabase as AsyncStandardDatabase
from pytest import fixture

from app.database.async_conn import AsyncConn
from app.database.conn import get_db
from config import settings

from tests.utils import async_restart_db, restart_db


def auth_test() -> dict:
    return {"username": settings.ARANGO_USERNAME, "password": settings.ARANGO_PASSWORD}


@fixture
def db():
    db: StandardDatabase = get_db("test")
    yield db
    restart_db(db)


# https://pytest-asyncio.readthedocs.io/en/latest/concepts.html
# "It’s highly recommended for neighboring tests to use the same event loop scope"
@pytest_asyncio.fixture(loop_scope="session")
async def async_db():
    async_db: AsyncStandardDatabase = await AsyncConn.async_get_db("test_async")
    yield async_db
    await async_restart_db(async_db)
