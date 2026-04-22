import re
from abc import ABC, abstractmethod
from typing import Literal, Self

from app.aql.elements import FieldFor
from app.aql.schemas import ForGraphData, GraphResponse
from app.aql.snippets import aql_return_graph
from app.mapper.expressions import FieldDescriptor, GroupLogicalConnector, Matcher
from app.mapper.types import T, TEdge


class AQLOperation(ABC):
    @property
    @abstractmethod
    def bind_vars(self) -> dict: ...

    @abstractmethod
    def aql(self, subfix: str = "") -> str: ...

    def _build_bind_var(self, prefix: str, subfix: str) -> str:
        return f"{prefix}__{subfix}"


class Filter(AQLOperation, ABC):
    def __init__(self, condition: Matcher | GroupLogicalConnector) -> None:
        self.condition: Matcher | GroupLogicalConnector = condition
        self._bind_vars: dict = {}
        self._counter: int = 0

    @property
    def bind_vars(self) -> dict:
        return self._bind_vars

    def aql(self, subfix: str = "") -> str:
        def recursive(condition: Matcher | GroupLogicalConnector):
            if isinstance(condition, GroupLogicalConnector):
                left = recursive(condition.left)
                connector = condition.connector
                right = recursive(condition.right)
                return f"({left} {connector} {right})"
            else:
                self._counter += 1
                response = self.extract_field(condition)
                is_raw, value = self._extract_value(condition.value)

                if is_raw:
                    bind_var = self._build_bind_var(
                        f"{condition.field.target}_{self._counter}", subfix
                    )
                    self._bind_vars[bind_var] = condition.value
                    response += f"@{bind_var}"
                else:
                    response += value

                return response

        return f"FILTER {res} " if (res := recursive(self.condition)) else ""

    @abstractmethod
    def extract_field(self, cond: Matcher) -> str: ...

    def _extract_value(self, value: any) -> tuple[bool, any]:
        if isinstance(value, FieldFor):
            return False, value.value
        elif isinstance(value, Let):
            return False, value.name
        return True, value


class ForFilter(Filter):
    def __init__(self, cond: Matcher | GroupLogicalConnector, alias: str):
        super().__init__(cond)
        self.alias: str = alias

    def extract_field(self, cond: Matcher) -> str:
        return f"{self.alias}.{cond.field.target} {cond.operator} "


class ForGraphFilter(Filter):
    def __init__(self, cond: Matcher | GroupLogicalConnector, data: ForGraphData):
        super().__init__(cond)
        self.data: ForGraphData = data

    def extract_field(self, cond: Matcher) -> str:
        alias = ""

        if cond.field.model == self.data.edge:
            alias = self.data.e_alias
        elif cond.field.model == self.data.collection:
            alias = self.data.v_alias

        return f"{alias}.{cond.field.target} {cond.operator} "


class For(AQLOperation):
    def __init__(self, collection: type[T], alias: str = "doc"):
        self.collection: type[T] = collection
        self.alias: str = alias
        self._list_operation: list[Let | ForFilter | ForGraphFilter] = []
        self._filter: Filter | None = None  # Borrar
        self._response: str | None = None
        self._bind_vars: dict = {}

    def add_let(self, op_let: Let) -> Self:
        self._list_operation.append(op_let)
        return self

    def filter(self, cond: Matcher | GroupLogicalConnector) -> Self:
        self._list_operation.append(ForFilter(cond, self.alias))
        return self

    @property
    def bind_vars(self) -> dict:
        return self._bind_vars

    def aql(self, subfix: str = "") -> str:
        self._bind_vars: dict = {}

        query: str = f"FOR {self.alias} IN {self.collection._collection_name} "
        counter: int = 0

        for operation in self._list_operation:
            counter += 1
            query += operation.aql(f"{subfix}__{counter}")
            self._bind_vars |= operation.bind_vars

        query += f"RETURN {self._response} " if self._response else ""
        return query

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


class ForGraph(For):
    def __init__(
        self,
        start: T,
        direction: Literal["OUTBOUND", "INBOUND", "ANY"],
        graph: type[TEdge],
        min_p: int = 1,
        max_p: int = 1,
        v_alias: str = "vertex",
        e_alias: str = "edge",
        p_alias: str = "path",
    ):
        self.start = start
        self.direction = direction
        self._min: int = min_p
        self._max: int = max_p
        self.graph_data = ForGraphData(
            collection=type(start),
            edge=graph,
            v_alias=v_alias,
            e_alias=e_alias,
            p_alias=p_alias,
        )

        super().__init__(GraphResponse[self.graph_data.collection, graph])

    def filter(self, condition: Matcher | GroupLogicalConnector) -> Self:
        self._list_operation.append(ForGraphFilter(condition, self.graph_data))
        return self

    def aql(self, subfix: str = "") -> str:
        self._bind_vars: dict = {}

        alias: str = f"{self.graph_data.v_alias}, {self.graph_data.e_alias}, {self.graph_data.p_alias}"
        depth: str = f"{self._min}..{self._max}"
        start: str = self.start.id
        query: str = f"FOR {alias} IN {depth} {self.direction} '{start}' GRAPH {self.graph_data.graph_name} "
        counter: int = 0

        for operation in self._list_operation:
            counter += 1
            query += operation.aql(f"{subfix}__{counter}")
            self._bind_vars |= operation.bind_vars

        return query

    def aql_return(self) -> str:
        return aql_return_graph(
            self.graph_data.v_alias, self.graph_data.e_alias, self.graph_data.p_alias
        )
