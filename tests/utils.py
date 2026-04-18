import inspect

from arango.database import StandardDatabase

from app import collections


def restart_db(db: StandardDatabase):
    for _, collection in inspect.getmembers(collections, inspect.isclass):
        if collection._collection_name:
            db.collection(collection._collection_name).truncate()
