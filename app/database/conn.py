from typing import Callable

from arango import ArangoClient
from arango.database import StandardDatabase, TransactionDatabase
from loguru import logger

from app.database.migrate import sync_migration
from config import settings

_client: ArangoClient | None = None
_db: StandardDatabase | None = None


def get_db() -> StandardDatabase:
    global _client, _db

    if _db is not None:
        return _db

    _client = ArangoClient(hosts=f"{settings.ARANGO_HOST}:{settings.ARANGO_PORT}")
    _db = _client.db(
        settings.ARANGO_DB,
        username=settings.ARANGO_USERNAME,
        password=settings.ARANGO_PASSWORD,
        verify=True,
    )

    logger.success(f"Start connection to '{settings.ARANGO_DB}' database")

    sync_migration(_db)

    return _db


def execute_transaction(
    process: Callable, read: list[str] = [], write: list[str] = []
) -> any:
    """https://docs.python-arango.com/en/main/transaction.html"""

    db: StandardDatabase = get_db()
    txn: TransactionDatabase | None = None

    try:
        txn = db.begin_transaction(read=read, write=write)
        tid = txn.transaction_id

        logger.info(f"Start transaction '{tid}'")

        response = process(txn)
        txn.commit_transaction()

        logger.info(f"Close transaction '{tid}'")

        return response
    except Exception as _:
        if txn is None:
            raise

        txn.abort_transaction()
        logger.error(f"Abort transaction '{tid}'")
        raise
