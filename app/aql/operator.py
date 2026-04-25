import re
from abc import ABC, abstractmethod
from typing import Literal, Self

from app.aql.elements import FieldFor
from app.aql.schemas import ForGraphData, GraphResponse
from app.aql.snippets import (
    aql_return_graph,
    aql_return_graph_edge,
)
from app.mapper.expressions import (
    FieldDescriptor,
    GroupLogicalConnector,
    Matcher,
    RawExpression,
)
from app.mapper.types import T, TEdge


class AQLOperation(ABC):
    @property
    @abstractmethod
    def bind_vars(self) -> dict:
        """
        Dictionary of bind variables required for this operation.
        """
        ...

    @abstractmethod
    def aql(self, subfix: str = "") -> str:
        """
        Generate the AQL string fragment for this operation.

        Args:
            subfix: Optional suffix to ensure unique bind variable names.
        """
        ...

    def _build_bind_var(self, prefix: str, subfix: str) -> str:
        return f"{prefix}__{subfix}"


class Raw(AQLOperation, RawExpression):
    def __init__(self, query: str, bind_vars: dict = {}):
        """
        Initialize a raw AQL fragment.

        Args:
            query: The literal AQL code string.
            bind_vars: Initial dictionary of bind variables.
        """
        self.query: str = query
        self._bind_vars: dict = bind_vars
        self._updated_bind_vars: dict = {}

    @property
    def bind_vars(self) -> dict:
        return self._updated_bind_vars

    def aql(self, subfix: str) -> str:
        return self._update_bind_vars(subfix)

    def _update_bind_vars(self, subfix: str) -> str:
        """
        Avoid collisions of the same names.
        """
        query_updated = self.query

        for key, val in self._bind_vars.items():
            bind_var = self._build_bind_var(key, subfix)
            pattern = rf"@{key}\b"
            query_updated = re.sub(pattern, f"@{bind_var}", query_updated)
            self._updated_bind_vars[bind_var] = val

        return query_updated


class Filter(AQLOperation, ABC):
    def __init__(self, condition: Matcher | GroupLogicalConnector) -> None:
        self.condition: Matcher | GroupLogicalConnector = condition
        self._bind_vars: dict = {}
        self._counter: int = 0

    @property
    def bind_vars(self) -> dict:
        return self._bind_vars

    def aql(self, subfix: str = "") -> str:
        self._bind_vars = {}
        self._counter = 0

        def recursive(cond: Matcher | GroupLogicalConnector | Raw):
            if isinstance(cond, GroupLogicalConnector):
                left = recursive(cond.left)
                connector = cond.connector
                right = recursive(cond.right)
                return f"({left} {connector} {right})"
            else:
                return self._extract_field_and_value(cond, subfix)

        return f" FILTER {res} " if (res := recursive(self.condition)) else ""

    def _extract_field_and_value(self, cond: Raw | Matcher, subfix: str = "") -> str:
        self._counter += 1

        if isinstance(cond, Matcher):
            return self._extract_matcher(cond, subfix)
        return self._extract_raw(cond, subfix)

    def _extract_matcher(self, matcher: Matcher, subfix: str = "") -> str:
        response: str = self.extract_field(matcher)
        is_input, value = self._extract_value(matcher.value)

        if is_input:
            bind_var = self._build_bind_var(
                f"{matcher.field.target}_{self._counter}", subfix
            )
            self._bind_vars[bind_var] = matcher.value
            response += f"@{bind_var}"
        else:
            response += value

        return response

    def _extract_raw(self, raw: Raw, subfix: str = "") -> str:
        response = raw.aql(f"{self._counter}_raw_{subfix}")
        self._bind_vars |= raw.bind_vars
        return response

    @abstractmethod
    def extract_field(self, cond: Matcher) -> str:
        """
        Extract and format the field reference from a Matcher condition.

        Args:
            cond: Matcher instance containing the field and operator logic.

        Returns:
            str: The AQL-ready string representation of the field.
        """
        ...

    def _extract_value(self, value: any) -> tuple[bool, any]:
        if isinstance(value, FieldFor):
            return False, value.value
        elif isinstance(value, Let):
            return False, value.name
        elif isinstance(value, Raw):
            res = value.aql(self._counter)
            self._bind_vars |= value.bind_vars
            return False, res
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
        elif cond.field.model in self.data.edge.get_edge_definition():
            alias = self.data.v_alias

        return f"{alias}.{cond.field.target} {cond.operator} "


class For(AQLOperation):
    def __init__(self, collection: type[T], alias: str = "doc"):
        """
        Initialize a "FOR" operator.
        Syntax: FOR "alias" in "collection".

        Args:
            collection: Collection class context.
            alias: Iter name, Defaults to "doc".
        """
        self.collection: type[T] = collection
        self.alias: str = alias
        self._list_operations: list[Let | ForFilter | ForGraphFilter | Raw] = []
        self._response: str | None = None
        self._bind_vars: dict = {}

    def add_raw(self, raw: Raw) -> Self:
        """
        Add raw aql to the query.

        Args:
            raw: "Raw" class instance representing the aql code.

        Returns:
            Self: The current "For" instance to allow method chaining.
        """
        self._list_operations.append(raw)
        return self

    def add_let(self, op_let: Let) -> Self:
        """
        Add the "LET" operator to the query.

        Args:
            op_let: "Let" class instance respsenting the variable.

        Returns:
            Self: The current "For" instance to allow method chaining.
        """
        self._list_operations.append(op_let)
        return self

    def filter(self, cond: Matcher | GroupLogicalConnector | Raw) -> Self:
        """
        Add the "FILTER" operator to the query.

        Args:
            cond: "Matcher" or  "GroupLogicalConnector" class instance representing
            the filter condition or a group of logical conditions.

        Returns:
            Self: The current "For" instance to allow method chaining.
        """
        self._list_operations.append(ForFilter(cond, self.alias))
        return self

    def field(self, field: FieldDescriptor) -> FieldFor:
        """
        Get a especified field of the current "FOR" instance.

        Args:
            field: "FieldDescriptor" instance representing the specific
                collection field.

        Returns:
            FieldFor: An instance of the field linked to this FOR's alias.
        """
        return FieldFor(self.alias, field)

    def subquery(self, field_response: FieldDescriptor) -> Self:
        """
        Convert the "FOR" operation into a subquery that returns a specific field.

        Args:
            field_response: FieldDescriptor instance representing the field
                to be returned by the subquery.

        Returns:
            Self: The current instance, now configured to be rendered as a subquery.
        """
        self._response = f"{self.alias}.{field_response.target}"
        return self

    def subquery_raw(self, raw: Raw) -> Self:
        """
        Convert the "FOR" operation into a subquery that returns aql.

        Args:
            raw: "Raw" class instance representing the aql code.

        Returns:
            Self: The current instance, now configured to be rendered as a subquery.
        """
        self._response = raw.aql("")
        return self

    @property
    def bind_vars(self) -> dict:
        return self._bind_vars

    def aql(self, subfix: str = "") -> str:
        self._bind_vars = {}

        query: str = f" FOR {self.alias} IN {self.collection._collection_name} "
        counter: int = 0

        for operation in self._list_operations:
            counter += 1
            query += operation.aql(f"{subfix}__{counter}")
            self._bind_vars |= operation.bind_vars

        if self._response:
            query += f" RETURN {self._response} "
            return f"({query})"

        return query


class Let(AQLOperation):
    def __init__(self, name: str, value: For | Raw):
        """
        Initialize a "LET" operator.

        Args:
            name: The name of the variable ot be defined in AQL.
            value: The value to assign. Can be a "For" subquery or "Raw" expression.
        """
        self.name: str = name
        self.value: For | Raw = value

    @property
    def bind_vars(self) -> dict:
        return self.value.bind_vars

    def aql(self, subfix: str = "") -> str:
        return f"LET {self.name} = {self.value.aql(subfix)} "


class ForGraph(For):
    def __init__(
        self,
        start: T,
        direction: Literal["OUTBOUND", "INBOUND", "ANY"],
        graph: type[TEdge],
        min_d: int = 1,
        max_d: int = 1,
        v_alias: str = "vertex",
        e_alias: str = "edge",
        p_alias: str = "path",
    ):
        """
        Initialize a "FOR .. GRAPH .." operator.
        Syntax: FOR {v_alias}, {e_alias}, {p_alias} in {min_d..max_d} {direction} {start} GRAPH {graph}

        Args:
            start: Collection class instance to start.
            direction: Traversal direction: "OUTBOUND", "INBOUND", or "ANY".
            graph: Edge collection.
            min_d: Minimum traversal depth. Defaults to 1.
            max_d: Maximum traversal depth. Defaults to 1.
            v_alias: Alias for the vertex. Defaults to "vertex".
            e_alias: Alias for the edge. Defaults to "edge".
            p_alias: Alias for the path. Defaults to "path".
        """
        self.start = start
        self.direction = direction
        self._min: int = min_d
        self._max: int = max_d
        self.graph_data = ForGraphData(
            edge=graph,
            v_alias=v_alias,
            e_alias=e_alias,
            p_alias=p_alias,
        )
        vfrom, vto = graph.get_edge_definition()
        super().__init__(GraphResponse[vfrom | vto, graph])

    def filter(self, cond: Matcher | GroupLogicalConnector | Raw) -> Self:
        """
        Add the "FILTER" operator to the query.

        Args:
            cond: "Matcher", "GroupLogicalConnector" or "Raw" class instance representing
            the filter condition, a group of logical conditions or aql raw.

        Returns:
            Self: The current "ForGraph" instance to allow method chaining.
        """
        self._list_operations.append(ForGraphFilter(cond, self.graph_data))
        return self

    def field(self, field: FieldDescriptor) -> FieldFor:
        """
        Get a especified field of the current "FOR GRAPH" instance.

        Args:
            field: "FieldDescriptor" instance representing the specific
                collection field.

        Returns:
            FieldFor: An instance of the field linked to this FOR GRAPH's alias.
        """
        if field.model in self.graph_data.edge.get_edge_definition():
            return FieldFor(self.graph_data.v_alias, field)
        else:
            return FieldFor(self.graph_data.e_alias, field)

    def subquery(self, field_response: FieldDescriptor) -> Self:
        """
        Convert the "FOR GRAPH" operation into a subquery that returns a specific field.

        Args:
            field_response: FieldDescriptor instance representing the field
                to be returned by the subquery.

        Returns:
            Self: The current instance, now configured to be rendered as a subquery.
        """
        if field_response.model in self.graph_data.edge.get_edge_definition():
            self._response = f"{self.graph_data.v_alias}.{field_response.target}"
        else:
            self._response = f"{self.graph_data.e_alias}.{field_response.target}"
        return self

    def return_edge(self) -> Raw:
        """
        Generate a 'Raw' expression to return edges hydrated with their vertices.

        This method builds an AQL fragment that merges edge data with
        the corresponding 'from' and 'to' vertex documents using a
        pre-calculated vertex map.

        Returns:
            Raw: A Raw class instance containing the AQL MERGE logic
                for the edge and its vertices.
        """
        aql_return, aql_raw = aql_return_graph_edge(
            self.graph_data.e_alias, self.graph_data.p_alias
        )

        self.add_raw(Raw(aql_raw))

        return Raw(aql_return)

    def return_vertex(self) -> Raw:
        """
        Generate a 'Raw' expression to return vertex.

        Returns:
            Raw: A Raw class instance containing the AQL vertex.
        """
        return self.graph_data.v_alias

    def aql(self, subfix: str = "") -> str:
        self._bind_vars: dict = {}

        alias: str = f"{self.graph_data.v_alias}, {self.graph_data.e_alias}, {self.graph_data.p_alias}"
        depth: str = f"{self._min}..{self._max}"
        start: str = self.start.id
        query: str = f" FOR {alias} IN {depth} {self.direction} '{start}' GRAPH {self.graph_data.graph_name} "
        counter: int = 0

        for operation in self._list_operations:
            counter += 1
            query += operation.aql(f"{subfix}__{counter}")
            self._bind_vars |= operation.bind_vars

        if self._response:
            query += f" RETURN {self._response} "
            return f"({query})"

        return query

    def aql_return(self) -> str:
        return aql_return_graph(
            self.graph_data.v_alias, self.graph_data.e_alias, self.graph_data.p_alias
        )
