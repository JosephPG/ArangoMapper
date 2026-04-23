from arango.database import StandardDatabase

from app.database.schemas import InsertCollection
from app.mapper.types import T, TEdge


class CollectionManager:
    def __init__(self, db: StandardDatabase):
        self.db = db

    def insert(self, instance: T):
        response: InsertCollection = self.db.collection(instance._collection_name).insert(
            self._prepare_insert_fields(instance)
        )
        self._fill_metada(instance, response)

    def insert_graph(self, instance: TEdge):
        graph = self.db.graph(instance._graph_name)
        response: InsertCollection = graph.link(
            instance._collection_name,
            instance.vertex_from.id,
            instance.vertex_to.id,
            data=self._prepare_insert_fields(instance),
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

    def _prepare_insert_fields(self, instance: T | TEdge) -> dict:
        exclude = set(x for x in ["id", "key"] if not getattr(instance, x))
        return instance.model_dump(by_alias=True, exclude=exclude)

    def _fill_metada(self, instance: T | TEdge, response: InsertCollection):
        instance.id = response["_id"]
        instance.key = response["_key"]
