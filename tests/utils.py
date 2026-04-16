from arango.database import StandardDatabase

from app import collections


def restart_db(db: StandardDatabase):
    for collection in collections.CollectionBase.__subclasses__():
        db.collection(collection._collection_name).truncate()
