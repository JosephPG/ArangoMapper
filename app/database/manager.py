from typing import TypeVar

from arango.database import StandardDatabase

from app.database.schemas import InsertCollection
from app.mapper.base import CollectionBase

T = TypeVar("T", bound=CollectionBase)


class CollectionManager:
    def __init__(self, db: StandardDatabase):
        self.db = db

    def insert(self, instance: T):
        response: InsertCollection = self.db.collection(instance._collection_name).insert(
            self._prepare_insert_fields(instance)
        )
        self._fill_metada(instance, response)

    def update(self, instance: T):
        self.db.collection(instance._collection_name).update(
            instance.model_dump(by_alias=True)
        )

    def insert_many(self, instances: list[T]):
        if not instances:
            return

        rows = [self._prepare_insert_fields(x) for x in instances]

        responses: list[InsertCollection] = self.db.collection(
            instances[0]._collection_name
        ).insert_many(rows)

        for instance, response in zip(instances, responses):
            self._fill_metada(instance, response)

    def _prepare_insert_fields(self, instance: T) -> dict:
        exclude = set(x for x in ["id", "key"] if not getattr(instance, x))
        return instance.model_dump(by_alias=True, exclude=exclude)

    def _fill_metada(self, instance: T, response: InsertCollection):
        instance.id = response["_id"]
        instance.key = response["_key"]
