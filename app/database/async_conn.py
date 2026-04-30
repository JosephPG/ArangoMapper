import asyncio

from arangoasync import ArangoClient
from arangoasync.auth import Auth
from arangoasync.database import StandardDatabase
from loguru import logger

from app.database.async_migrate import async_migration
from config import settings


class AsyncConn:
    """
    https://stackoverflow.com/questions/34510/what-is-a-race-condition
    https://docs.python.org/3/library/asyncio-sync.html
    """

    _client: ArangoClient | None = None
    _db: StandardDatabase | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def async_get_db(cls, db_name: str = settings.ARANGO_DB) -> StandardDatabase:
        if cls._db is not None:
            return cls._db

        async with cls._lock:
            print("Entro aca a pesar del lock")
            ops = {
                "auth": Auth(
                    username=settings.ARANGO_USERNAME,
                    password=settings.ARANGO_PASSWORD,
                ),
                "verify": True,
            }
            cls._client = ArangoClient(
                hosts=f"{settings.ARANGO_HOST}:{settings.ARANGO_PORT}"
            )
            sys_db = await cls._client.db("_system", **ops)

            if not await sys_db.has_database(db_name):
                await sys_db.create_database(db_name)

            cls._db = await cls._client.db(db_name, **ops)

            logger.success(f"Start async connection to '{db_name}' database")

            await async_migration(cls._db)

            return cls._db
