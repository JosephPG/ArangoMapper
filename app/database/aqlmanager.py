from typing import Self, TypeVar

from app.mapper.base import CollectionBase

T = TypeVar("T", bound=CollectionBase)


class AQLManager:
    pass


class For:
    def __init__(self, collection: type[T], alias: str = "doc"):
        self.collection: type[T] = collection
        self.alias: str = alias
        self._filter: str | None = None
        self._response: str | None = None

    def filter(self, value: str, **__) -> Self:
        self._filter = value
        return self

    def response(self, value: str = "", **__) -> Self:
        self._response = self.alias if not value else value
        return self

    def aql(self) -> str:
        query: str = f"FOR {self.alias} IN {self.collection._collection_name} "
        query += f"FILTER {self._filter} " if self._filter else ""
        query += f"RETURN {self._response}" if self._response else ""
        return query


class Let:
    def __init__(self, name: str, value: For | str):
        self.name: str = name
        self.value: For | str = value

    def aql(self) -> str:
        return f"LET {self.name} = ({self.data})"

    @property
    def data(self) -> str:
        return self.value.aql() if isinstance(self.value, For) else self.value
