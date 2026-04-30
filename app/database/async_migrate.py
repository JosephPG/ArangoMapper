import inspect

from arangoasync.database import StandardDatabase
from loguru import logger

from app import collections
from app.mapper.base import CollectionEdge
from app.mapper.types import T, TEdge


async def async_migration(db: StandardDatabase):
    for _, collection in inspect.getmembers(collections, inspect.isclass):
        if issubclass(collection, CollectionEdge):
            await start_graph(db, collection)
        else:
            await start_collection(db, collection)


async def start_graph(db: StandardDatabase, collection: type[TEdge]):
    if collection._collection_name and not await db.has_graph(collection._graph_name):
        graph = await db.create_graph(collection._graph_name)
        collection_from, collection_to = collection.get_edge_definition()

        await graph.create_edge_definition(
            edge_collection=collection._collection_name,
            from_vertex_collections=[collection_from._collection_name],
            to_vertex_collections=[collection_to._collection_name],
        )

        logger.info(f"New graph '{collection._graph_name}' created")


async def start_collection(db: StandardDatabase, collection: type[T]):
    if collection._collection_name and not await db.has_collection(
        collection._collection_name
    ):
        await db.create_collection(collection._collection_name)
        logger.info(f"New collection '{collection._collection_name}' created")
