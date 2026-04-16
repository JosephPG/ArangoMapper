from typing import TypeVar

from arango.database import StandardDatabase

from app.layer.base import CollectionBase

T = TypeVar("T", bound=CollectionBase)


class CollectionManager:
    def __init__(self, db: StandardDatabase):
        self.db = db

    def insert(self, instance: T):
        self.db.collection(instance._collection_name).insert(
            instance.model_dump(by_alias=True)
        )

    def insert_many(self, instances: list[T]):
        if not instances:
            return

        rows = [x.model_dump(by_alias=True) for x in instances]
        collection_name = instances[0]._collection_name
        self.db.collection(collection_name).insert_many(rows)
