import inspect
from typing import TypeVar

from arango.database import StandardDatabase
from loguru import logger

from app import collections
from app.mapper.base import CollectionBase, CollectionEdge

TBase = TypeVar("TBase", bound=CollectionBase)
TEdge = TypeVar("TEdge", bound=CollectionEdge)


def sync_migration(db: StandardDatabase):
    for class_name, collection in inspect.getmembers(collections, inspect.isclass):
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


def start_collection(db: StandardDatabase, collection: type[TBase]):
    if collection._collection_name and not db.has_collection(collection._collection_name):
        db.create_collection(collection._collection_name)
        logger.info(f"New collection '{collection._collection_name}' created")
