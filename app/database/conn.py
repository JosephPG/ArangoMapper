from arango import ArangoClient
from arango.database import StandardDatabase
from loguru import logger

from config import settings

_client: ArangoClient | None = None
_db: StandardDatabase | None = None


def get_db() -> StandardDatabase:
    global _client, _db

    if _db is not None:
        return _db

    _client = ArangoClient(hosts=settings.arango_host)
    _db = _client.db(
        settings.arango_db,
        username=settings.arango_username,
        password=settings.arango_password,
        verify=True,
    )

    logger.success(f"Start connection to '{settings.arango_db}' database")

    return _db
