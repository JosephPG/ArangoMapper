from arango import ArangoClient
from arango.database import StandardDatabase
from loguru import logger

from app import collections
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

    start_collections()

    return _db


def start_collections():
    for collection in collections.Base.__subclasses__():
        if not _db.has_collection(collection._collection_name):
            _db.create_collection(collection._collection_name)
            logger.info(f"New collection '{collection._collection_name}' created")
