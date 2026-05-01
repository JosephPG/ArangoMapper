import inspect
from importlib import import_module
from typing import TypeVar

from arango.database import StandardDatabase
from arangoasync.database import StandardDatabase as AsyncStandardDatabase
from loguru import logger

from arangomapper.mapper.base import CollectionBase
from config import MIGRATE_MODELS

T = TypeVar("T", bound=CollectionBase)


def inspect_collections():
    try:
        for path in MIGRATE_MODELS:
            module = import_module(path)
            for _, collection in inspect.getmembers(module, inspect.isclass):
                if collection._collection_name:
                    yield collection
    except ModuleNotFoundError as _:
        logger.error(f"{path} module not found")


def truncate_collection(db: StandardDatabase, collection: CollectionBase):
    db.collection(collection._collection_name).truncate()


def restart_db(db: StandardDatabase):
    for collection in inspect_collections():
        truncate_collection(db, collection)


async def async_truncate_collection(
    db: AsyncStandardDatabase, collection: CollectionBase
):
    await db.collection(collection._collection_name).truncate()


async def async_restart_db(db: AsyncStandardDatabase):
    for collection in inspect_collections():
        await async_truncate_collection(db, collection)
