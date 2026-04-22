from typing import Literal, Self, TypeVar

from arango.database import StandardDatabase

from app.aql.elements import FieldFor, Limit, Sort
from app.aql.operator import For, ForGraph, Let
from app.aql.snippets import aql_return_edge
from app.mapper.base import CollectionBase, CollectionEdge

T = TypeVar("T", bound=CollectionBase)


class AQLManager:
    def __init__(self, db: StandardDatabase):
        self.db: StandardDatabase = db
        self._list_operations: list[For | Let | ForGraph] = []
        self._list_sort: list[Sort] = []
        self._limit: Limit | None = None
        self._bind_vars: dict = {}
        self._last_for: For

    def add_let(self, op_let: Let) -> Self:
        self._list_operations.append(op_let)
        return self

    def add_for(self, op_for: For | ForGraph) -> Self:
        self._list_operations.append(op_for)
        self._last_for = op_for
        return self

    def add_sort(self, field: FieldFor, order: Literal["asc", "desc"] = "asc") -> Self:
        self._list_sort.append(Sort(field, order))
        return self

    def limit(self, count: int, offset: int | None = None) -> Self:
        self._limit = Limit(count, offset)
        return self

    def list(self) -> list[T]:
        cursor = self.db.aql.execute(self.aql(), bind_vars=self._bind_vars)
        return [self._last_for.collection(**x) for x in cursor]

    def aql(self) -> str:
        self._bind_vars: dict = {}
        query: str = ""
        counter: int = 0

        for operation in self._list_operations:
            counter += 1
            query += operation.aql(counter)
            self._bind_vars |= operation.bind_vars

        query += self._aql_sort()
        query += self._limit.aql() if self._limit else ""
        query += self._aql_return()

        return query

    def _aql_sort(self) -> str:
        if not self._list_sort:
            return ""

        return "SORT {} ".format(", ".join([x.aql() for x in self._list_sort]))

    def _aql_return(self) -> str:
        alias = self._last_for.alias

        if isinstance(self._last_for, ForGraph):
            return self._last_for.aql_return()
        elif issubclass(self._last_for.collection, CollectionEdge):
            return aql_return_edge(alias)

        return f"RETURN {alias}"
