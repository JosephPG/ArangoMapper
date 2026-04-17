from arango import ArangoClient
from arango.database import StandardDatabase
from loguru import logger

from app.database.migrate import sync_migration
from config import settings

_client: ArangoClient | None = None
_db: StandardDatabase | None = None


def get_db() -> StandardDatabase:
    global _client, _db

    if _db is not None:
        return _db

    _client = ArangoClient(hosts=settings.ARANGO_HOST)
    _db = _client.db(
        settings.ARANGO_DB,
        username=settings.ARANGO_USERNAME,
        password=settings.ARANGO_PASSWORD,
        verify=True,
    )

    logger.success(f"Start connection to '{settings.ARANGO_DB}' database")

    sync_migration(_db)

    return _db
