import re
from abc import ABC, abstractmethod
from typing import Literal, Self, TypeVar

from arango.database import StandardDatabase

from app.mapper.base import CollectionBase, CollectionEdge
from app.mapper.expressions import FieldDescriptor, GroupLogicalConnector, Matcher

T = TypeVar("T", bound=CollectionBase)


class FieldFor:
    def __init__(self, alias: str, field: FieldDescriptor):
        self.alias: str = alias
        self.field: FieldDescriptor = field

    @property
    def value(self) -> str:
        return f"{self.alias}.{self.field.target}"


class Sort:
    def __init__(self, field: FieldFor, order: Literal["asc", "desc"]):
        self.field: FieldFor = field
        self.order: Literal["asc", "desc"] = order

    def aql(self) -> str:
        return f"{self.field.value} {self.order.upper()}"


class Limit:
    def __init__(self, count: int, offset: int | None = None):
        self.count: int = count
        self.offset: int | None = offset

    def aql(self) -> str:
        if self.offset is not None:
            return f"LIMIT {self.offset}, {self.count} "
        return f"LIMIT {self.count} "


class AQLOperation(ABC):
    @property
    @abstractmethod
    def bind_vars(self) -> dict: ...

    @abstractmethod
    def aql(self, subfix: str = "") -> str: ...

    def _build_bind_var(self, prefix: str, subfix: str) -> str:
        return f"{prefix}__{subfix}"


class Filter(AQLOperation):
    def __init__(self, condition: Matcher | GroupLogicalConnector, alias: str) -> None:
        self.condition: Matcher | GroupLogicalConnector = condition
        self.alias = alias
        self._bind_vars: dict = {}
        self._counter: int = 0

    def aql(self, subfix: str = "") -> str:
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
                    bind_var = self._build_bind_var(
                        f"{condition.field.target}_{self._counter}", subfix
                    )
                    self._bind_vars[bind_var] = condition.value
                    response += f"@{bind_var}"
                else:
                    response += value

                return response

        return recursive(self.condition)

    @property
    def bind_vars(self) -> dict:
        return self._bind_vars

    def _extract_value(self, value: any) -> tuple[bool, any]:
        if isinstance(value, FieldFor):
            return False, value.value
        elif isinstance(value, Let):
            return False, value.name
        return True, value


class For(AQLOperation):
    def __init__(self, collection: type[T], alias: str = "doc"):
        self.collection: type[T] = collection
        self.alias: str = alias
        self._filter: Filter | None = None
        self._response: str | None = None

    @property
    def bind_vars(self) -> dict:
        return self._filter.bind_vars if self._filter else {}

    def aql(self, subfix: str = "") -> str:
        query: str = f"FOR {self.alias} IN {self.collection._collection_name} "
        query += f"FILTER {self._filter.aql(subfix)} " if self._filter else ""
        query += f"RETURN {self._response} " if self._response else ""
        return query

    def filter(self, condition: Matcher | GroupLogicalConnector) -> Self:
        self._filter = Filter(condition, self.alias)
        return self

    def field(self, field: FieldDescriptor) -> FieldFor:
        return FieldFor(self.alias, field)

    def subquery(self, field_response: FieldDescriptor) -> Self:
        self._response = f"{self.alias}.{field_response.target}"
        return self


class Let(AQLOperation):
    def __init__(self, name: str, value: For | str, bind_vars: dict = {}):
        self.name: str = name
        self.value: For | str = value
        self._bind_vars: dict = bind_vars

    @property
    def bind_vars(self) -> dict:
        return self.value.bind_vars if isinstance(self.value, For) else self._bind_vars

    def aql(self, subfix: str = "") -> str:
        return f"LET {self.name} = {self._value_aql(subfix)} "

    def _value_aql(self, subfix: str) -> str:
        if isinstance(self.value, For):
            return f"({self.value.aql(subfix)})"

        if "@" in self.value and not self.bind_vars:
            raise ValueError("Aql required bind_vars")

        self._update_bind_vars(subfix)

        return self.value

    def _update_bind_vars(self, subfix: str):
        """
        Avoid collisions of the same names
        """
        items = self._bind_vars.items()
        self._bind_vars = {}

        for key, val in items:
            bind_var = self._build_bind_var(key, subfix)
            pattern = rf"@{key}\b"
            self.value = re.sub(pattern, f"@{bind_var}", self.value)
            self._bind_vars[bind_var] = val


class AQLManager:
    def __init__(self, db: StandardDatabase):
        self.db: StandardDatabase = db
        self._list_operations: list[For | Let] = []
        self._list_sort: list[Sort] = []
        self._limit: Limit | None = None
        self._bind_vars: dict = {}
        self._last_for: For

    def add_let(self, op_let: Let) -> Self:
        self._list_operations.append(op_let)
        return self

    def add_for(self, op_for: For) -> Self:
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
            self._bind_vars = self._bind_vars | operation.bind_vars

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
        query = "RETURN "

        if issubclass(self._last_for.collection, CollectionEdge):
            vfrom = f"'vertex_from': DOCUMENT({alias}._from),"
            vto = f"'vertex_to': DOCUMENT({alias}._to)"
            return query + f"MERGE({alias}, {{{vfrom}{vto}}})"

        return query + alias
