import inspect
from typing import TypeVar

from arango.database import StandardDatabase

from app import collections
from app.mapper.base import CollectionBase, CollectionEdge

T = TypeVar("T", bound=CollectionBase)


def restart_db(db: StandardDatabase):
    for _, collection in inspect.getmembers(collections, inspect.isclass):
        collection: CollectionBase = collection
        if collection._collection_name:
            db.collection(collection._collection_name).truncate()


def delete_all_in_db(db: StandardDatabase):
    """
    Remove all graphs, edges, and collections, order required:
    1- graph
    2- edge
    3- collections
    """
    simple_collections: list[type[T]] = []

    for _, collection in inspect.getmembers(collections, inspect.isclass):
        collection: type[T] = collection

        if not collection._collection_name:
            continue
        if issubclass(collection, CollectionEdge):
            db.delete_graph(collection._graph_name, True)
            db.delete_collection(collection._collection_name, True)
        elif issubclass(collection, CollectionBase):
            simple_collections.append(collection)

    for simple_collection in simple_collections:
        db.delete_collection(simple_collection._collection_name, True)
