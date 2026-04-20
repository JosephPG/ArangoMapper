from typing import Self, TypeVar

from arango.database import StandardDatabase

from app.mapper.base import CollectionBase, CollectionEdge
from app.mapper.expressions import FieldDescriptor, GroupLogicalConnector, Matcher

T = TypeVar("T", bound=CollectionBase)


class FieldFor:
    def __init__(self, alias: str, field: FieldDescriptor):
        self.alias: str = alias
        self.field: FieldDescriptor = field


class Filter:
    def __init__(self, condition: Matcher | GroupLogicalConnector, alias: str) -> None:
        self.condition: Matcher | GroupLogicalConnector = condition
        self.alias = alias
        self.bind_vars: dict = {}
        self._counter: int = 0

    def aql(self):
        def recursive(condition: Matcher | GroupLogicalConnector):
            if isinstance(condition, GroupLogicalConnector):
                left = recursive(condition.left)
                connector = condition.connector
                right = recursive(condition.right)
                return f"({left} {connector} {right})"
            else:
                self._counter += 1
                is_raw, value = self._extract_value(condition.value)
                response = f"{self.alias}.{condition.field.target} {condition.operator} "

                if is_raw:
                    bind_var = f"{condition.field.target}_{self._counter}"
                    self.bind_vars[bind_var] = condition.value
                    response += f"@{bind_var}"
                else:
                    response += value

                return response

        return recursive(self.condition)

    def _extract_value(self, value: any) -> tuple[bool, any]:
        if isinstance(value, FieldFor):
            return False, f"{value.alias}.{value.field.target}"
        return True, value


class For:
    def __init__(self, collection: type[T], alias: str = "doc"):
        self.collection: type[T] = collection
        self.alias: str = alias
        self._filter: Filter | None = None

    @property
    def bind_vars(self) -> dict:
        return self._filter.bind_vars if self._filter else None

    def filter(self, condition: Matcher | GroupLogicalConnector) -> Self:
        self._filter = Filter(condition, self.alias)
        return self

    def field(self, field: FieldDescriptor) -> FieldFor:
        return FieldFor(self.alias, field)

    def aql(self) -> str:
        query: str = f"FOR {self.alias} IN {self.collection._collection_name} "
        query += f"FILTER {self._filter.aql()} " if self._filter else ""
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


class AQLManager:
    def __init__(self, db: StandardDatabase):
        self.db: StandardDatabase = db
        self.list_for: list[For] = []
        self._bind_vars: dict = {}
        self._last_for: For

    def add_for(self, s_for: For) -> Self:
        self.list_for.append(s_for)
        self._last_for = s_for
        return self

    def list(self) -> list[T]:
        cursor = self.db.aql.execute(self.aql(), bind_vars=self._bind_vars)
        return [self._last_for.collection(**x) for x in cursor]

    def aql(self) -> str:
        self._bind_vars: dict = {}
        query: str = ""

        for sentence_for in self.list_for:
            query += sentence_for.aql()
            self._bind_vars = self._bind_vars | sentence_for.bind_vars

        query += self._aql_return()
        return query

    def _aql_return(self) -> str:
        alias = self._last_for.alias
        query = "RETURN "

        if issubclass(self._last_for.collection, CollectionEdge):
            vfrom = f"'vertex_from': DOCUMENT({alias}._from),"
            vto = f"'vertex_to': DOCUMENT({alias}._to)"
            return query + f"MERGE({alias}, {{{vfrom}{vto}}})"

        return query + alias
