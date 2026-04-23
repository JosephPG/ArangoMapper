from typing import Literal, Self, TypeVar

from arango.cursor import Cursor
from arango.database import StandardDatabase
from pydantic import BaseModel

from app.aql.elements import FieldFor, Limit, Sort
from app.aql.operator import For, ForGraph, Let, Raw
from app.aql.snippets import aql_return_edge
from app.mapper.base import CollectionEdge
from app.mapper.types import T

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


class AQLManager:
    def __init__(self, db: StandardDatabase):
        self.db: StandardDatabase = db
        self._list_operations: list[For | Let | ForGraph] = []
        self._list_sort: list[Sort] = []
        self._limit: Limit | None = None
        self._bind_vars: dict = {}
        self._last_for: For
        self._return_model: type[TBaseModel] | None = None
        self._return_value: str | None = None
        self._return_bind_vars: dict = {}

    def add_let(self, op_let: Let) -> Self:
        self._list_operations.append(op_let)
        return self

    def add_for(self, op_for: For | ForGraph) -> Self:
        self._list_operations.append(op_for)
        self._last_for = op_for
        self._return_model = op_for.collection
        return self

    def add_sort(self, field: FieldFor, order: Literal["asc", "desc"] = "asc") -> Self:
        self._list_sort.append(Sort(field, order))
        return self

    def limit(self, count: int, offset: int | None = None) -> Self:
        self._limit = Limit(count, offset)
        return self

    def review(self) -> tuple[str, dict]:
        return self._aql(), self._bind_vars

    def get_by_id_or_key(self, collection: type[T], value: str) -> T | None:
        self.add_for(
            For(collection).filter((collection.id == value) | (collection.key == value))
        )
        return self.first()

    def list(self) -> list[T | dict | str | int | float | TBaseModel]:
        cursor: Cursor = self.db.aql.execute(self._aql(), bind_vars=self._bind_vars)
        return [self._return_model(**x) if self._return_model else x for x in cursor]

    def first(self) -> T | dict | str | int | float | TBaseModel | None:
        query = f"RETURN FIRST({self._aql()})"
        return self._cursor_one_element(query)

    def last(self) -> T | dict | str | int | float | TBaseModel | None:
        query = f"RETURN LAST({self._aql()})"
        return self._cursor_one_element(query)

    def return_raw(self, data: Raw, return_model: type[TBaseModel] | None = None) -> Self:
        self._return_model = return_model
        self._return_value = data.aql("__return")
        self._return_bind_vars = data.bind_vars
        return self

    def _cursor_one_element(self, query: str) -> T | dict | str | int | float | None:
        cursor: Cursor = self.db.aql.execute(query, bind_vars=self._bind_vars)

        if cursor.empty():
            return None

        data = cursor.pop()
        return self._return_model(**data) if self._return_model else data

    def _aql(self) -> str:
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
        if self._return_value:
            self._bind_vars |= self._return_bind_vars
            return f"RETURN {self._return_value}"

        alias = self._last_for.alias

        if isinstance(self._last_for, ForGraph):
            return self._last_for.aql_return()
        elif issubclass(self._last_for.collection, CollectionEdge):
            return aql_return_edge(alias)

        return f"RETURN {alias}"
