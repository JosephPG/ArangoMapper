import inspect
from importlib import import_module

from arango.database import StandardDatabase
from loguru import logger

from app.mapper.base import CollectionEdge
from app.mapper.types import T, TEdge
from config import MIGRATE_MODELS


def sync_migration(db: StandardDatabase):
    for path in MIGRATE_MODELS:
        try:
            inspect_module(db, import_module(path))
        except ModuleNotFoundError as _:
            logger.error(f"{path} module not found")


def inspect_module(db: StandardDatabase, module):
    for _, collection in inspect.getmembers(module, inspect.isclass):
        if issubclass(collection, CollectionEdge):
            start_graph(db, collection)
        else:
            start_collection(db, collection)


def start_graph(db: StandardDatabase, collection: type[TEdge]):
    if collection._collection_name and not db.has_graph(collection._graph_name):
        graph = db.create_graph(collection._graph_name)
        collection_from, collection_to = collection.get_edge_definition()

        graph.create_edge_definition(
            edge_collection=collection._collection_name,
            from_vertex_collections=[collection_from._collection_name],
            to_vertex_collections=[collection_to._collection_name],
        )

        logger.info(f"New graph '{collection._graph_name}' created")


def start_collection(db: StandardDatabase, collection: type[T]):
    if collection._collection_name and not db.has_collection(collection._collection_name):
        db.create_collection(collection._collection_name)
        logger.info(f"New collection '{collection._collection_name}' created")
