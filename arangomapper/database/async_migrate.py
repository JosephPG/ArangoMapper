from arangoasync.database import StandardDatabase
from loguru import logger

from arangomapper.database.utils import inspect_collections
from arangomapper.mapper.base import CollectionEdge
from arangomapper.mapper.types import T, TEdge


async def async_migration(db: StandardDatabase):
    for collection in inspect_collections():
        if issubclass(collection, CollectionEdge):
            await start_graph(db, collection)
        await start_collection(db, collection)


async def start_graph(db: StandardDatabase, collection: type[TEdge]):
    if not await db.has_graph(collection._graph_name):
        graph = await db.create_graph(collection._graph_name)
        collection_from, collection_to = collection.get_edge_definition()

        await graph.create_edge_definition(
            edge_collection=collection._collection_name,
            from_vertex_collections=[collection_from._collection_name],
            to_vertex_collections=[collection_to._collection_name],
        )

        logger.info(f"New graph '{collection._graph_name}' created")


async def start_collection(db: StandardDatabase, collection: type[T]):
    if not await db.has_collection(collection._collection_name):
        await db.create_collection(collection._collection_name)
        logger.info(f"New collection '{collection._collection_name}' created")
