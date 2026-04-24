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
    _QUERY_CACHE: dict[str, str] = {}  # Query Template Caching

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
        """
        Add the "LET" operator to the query

        Args:
            op_let: "Let" class instance respsenting the variable.

        Returns:
            Self: The current "AQLManager" instance to allow method chaining.
        """
        self._list_operations.append(op_let)
        return self

    def add_for(self, op_for: For | ForGraph) -> Self:
        """
        Add the "FOR" operator to the query.

        Args:
            op_for: "For" or "ForGraph" class instance representing the iteration.

        Returns:
            Self: The current "AQLManager" instance to allow method chaining.
        """
        self._list_operations.append(op_for)
        self._last_for = op_for
        self._return_model = op_for.collection
        return self

    def add_sort(self, field: FieldFor, order: Literal["asc", "desc"] = "asc") -> Self:
        """
        Add the "SORT" operator to the query.

        Args:
            field: "FieldFor" class instance representing the field to sort by
            order: Sorting direction, either "asc" or "desc". Defaults to "asc".

        Returns:
            Self: The current "AQLManager" instance to allow method chaining.
        """
        self._list_sort.append(Sort(field, order))
        return self

    def add_raw(self, raw: Raw) -> Self:
        """
        Add raw aql to the query.

        Args:
            raw: "Raw" class instance representing the aql code.

        Returns:
            Self: The current "AQLManager" instance to allow method chaining.
        """
        self._list_operations.append(raw)
        return self

    def limit(self, count: int, offset: int | None = None) -> Self:
        """
        Add the "LIMIT" operator to the query.

        Args:
            count: The number of items to bring
            offset: Optional index from which to start bringing in the collections.
                Defaults to "None".

        Returns:
            Self: The current "AQLManager" instance to allow method chaining.
        """
        self._limit = Limit(count, offset)
        return self

    def return_raw(self, data: Raw, return_model: type[TBaseModel] | None = None) -> Self:
        """
        Add raw aql to the "RETURN" operator.

        Args:
            data: "Raw" class instance representing the aql code
            return_model: Optional model class to parse and validate the results.
                Defaults to "None".

        Returns:
            Self: The current "AQLManager" instance to allow method chaining.
        """
        self._return_model = return_model
        self._return_value = data.aql("__return")
        self._return_bind_vars = data.bind_vars
        return self

    def review(self) -> tuple[str, dict]:
        """
        Generate the AQL string and its bind variables.

        Returns:
            tuple: A tuple containing (aql_string, bind_vars_dict).
        """
        return self._aql(), self._bind_vars

    def get_by_id_or_key(self, collection: type[T], value: str) -> T | None:
        """
        Find a document by its _id or _key and set the context collection.

        Args:
            collection: Collection class representing the search context.
            value: The unique _id or _key to search.

        Returns:
            T | None: An instance of collection, or None if not found.
        """
        self.add_for(
            For(collection).filter((collection.id == value) | (collection.key == value))
        )
        return self.first()

    def list(self) -> list[T | dict | str | int | float | TBaseModel]:
        """
        Execute the constructed query and return the list of resulting documents.

        Returns:
            list[T | dict | str | int | float | TBaseModel]: A list of results,
                which can be model instances, dictionaries, or primitive types
                depending on the RETURN clause.
        """
        cursor: Cursor = self.db.aql.execute(self._aql(), bind_vars=self._bind_vars)
        res = [self._return_model(**x) if self._return_model else x for x in cursor]
        cursor.close()
        return res

    def count(self) -> int:
        """
        Execute the constructed query and return count of documents.

        Returns:
            int: Count of documents.
        """
        self._return_model = None
        self.add_raw(Raw("COLLECT WITH COUNT INTO total"))
        self.return_raw(Raw("total"))
        return self._cursor_one_element(self._aql())

    def first(self) -> T | dict | str | int | float | TBaseModel | None:
        """
        Execute the constructed query and return the first document.

        Returns:
            T | dict | str | int | float | TBaseModel | None: which can be model
                instance, dictionarie, or primitive type depending on the RETURN
                clause.
        """
        query = f" RETURN FIRST({self._aql()})"
        return self._cursor_one_element(query)

    def last(self) -> T | dict | str | int | float | TBaseModel | None:
        """
        Execute the constructed query and return the last document.

        Returns:
            T | dict | str | int | float | TBaseModel | None: which can be model
                instance, dictionarie, or primitive type depending on the RETURN
                clause.
        """
        query = f" RETURN LAST({self._aql()})"
        return self._cursor_one_element(query)

    def _cursor_one_element(self, query: str) -> T | dict | str | int | float | None:
        cursor: Cursor = self.db.aql.execute(query, bind_vars=self._bind_vars)

        if (data := next(cursor, None)) is None:
            return None

        res = self._return_model(**data) if self._return_model else data
        cursor.close()
        return res

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

        return " SORT {} ".format(", ".join([x.aql() for x in self._list_sort]))

    def _aql_return(self) -> str:
        if self._return_value:
            self._bind_vars |= self._return_bind_vars
            return f" RETURN {self._return_value}"

        alias = self._last_for.alias

        if isinstance(self._last_for, ForGraph):
            return self._last_for.aql_return()
        elif issubclass(self._last_for.collection, CollectionEdge):
            return aql_return_edge(alias)

        return f" RETURN {alias}"
