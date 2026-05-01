from contextlib import asynccontextmanager
from typing import TypeVar

from arangoasync.cursor import Cursor
from arangoasync.database import StandardDatabase
from pydantic import BaseModel

from arangomapper.aql.aqlmanager import AQLManagerBase
from arangomapper.aql.operator import For, Raw
from arangomapper.mapper.types import T

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


class AsyncAQLManager(AQLManagerBase):
    def __init__(self, db: StandardDatabase):
        self.db: StandardDatabase = db
        super().__init__()

    async def get_by_id_or_key(self, collection: type[T], value: str) -> T | None:
        """
        Async Find a document by its _id or _key and set the context collection.

        Args:
            collection: Collection class representing the search context.
            value: The unique _id or _key to search.

        Returns:
            T | None: An instance of collection, or None if not found.
        """
        self.add_for(
            For(collection).filter((collection.id == value) | (collection.key == value))
        )
        return await self.first()

    async def list(self) -> list[T | dict | str | int | float | TBaseModel]:
        """
        Async Execute the constructed query and return the list of resulting documents.

        Returns:
            list[T | dict | str | int | float | TBaseModel]: A list of results,
                which can be model instances, dictionaries, or primitive types
                depending on the RETURN clause.
        """
        async with self._execute() as cursor:
            return [
                self._return_model(**x) if self._return_model else x async for x in cursor
            ]

    async def count(self) -> int:
        """
        Async Execute the constructed query and return count of documents.

        Returns:
            int: Count of documents.
        """
        self._return_model = None
        self.add_raw(Raw("COLLECT WITH COUNT INTO total"))
        self.return_raw(Raw("total"))
        return await self._cursor_one_element(self._aql())

    async def first(self) -> T | dict | str | int | float | TBaseModel | None:
        """
        Async Execute the constructed query and return the first document.

        Returns:
            T | dict | str | int | float | TBaseModel | None: which can be model
                instance, dictionarie, or primitive type depending on the RETURN
                clause.
        """
        query = f" RETURN FIRST({self._aql()})"
        return await self._cursor_one_element(query)

    async def last(self) -> T | dict | str | int | float | TBaseModel | None:
        """
        Async Execute the constructed query and return the last document.

        Returns:
            T | dict | str | int | float | TBaseModel | None: which can be model
                instance, dictionarie, or primitive type depending on the RETURN
                clause.
        """
        query = f" RETURN LAST({self._aql()})"
        return await self._cursor_one_element(query)

    async def _cursor_one_element(
        self, query: str
    ) -> T | dict | str | int | float | None:
        async with self._execute(batch_size=1, query=query) as cursor:
            data: Cursor = await cursor.next()

            if data is None:
                return None

            res = self._return_model(**data) if self._return_model else data
            return res

    @asynccontextmanager
    async def _execute(self, batch_size=100, query: str | None = None):
        try:
            self._data_generated = query or self._aql(), self._bind_var.data

            aql, bind_vars = self._data_generated

            cursor: Cursor = await self.db.aql.execute(
                aql, bind_vars=bind_vars, batch_size=batch_size
            )

            yield cursor
            await cursor.close()
        except Exception as _:
            raise
        finally:
            self._init_fields()
