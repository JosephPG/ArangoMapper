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

    _client = ArangoClient(hosts=settings.ARANGO_HOST)
    _db = _client.db(
        settings.ARANGO_DB,
        username=settings.ARANGO_USERNAME,
        password=settings.ARANGO_PASSWORD,
        verify=True,
    )

    logger.success(f"Start connection to '{settings.ARANGO_DB}' database")

    start_collections()

    return _db


def start_collections():
    for collection in collections.CollectionBase.__subclasses__():
        if not _db.has_collection(collection._collection_name):
            _db.create_collection(collection._collection_name)
            logger.info(f"New collection '{collection._collection_name}' created")
