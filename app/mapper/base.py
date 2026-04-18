from types import get_original_bases
from typing import ClassVar, Generic, TypeVar

from pydantic import BaseModel, Field
from pydantic._internal._generics import get_args

from app.mapper.meta import CollectionMetaClass

TFrom = TypeVar("TFrom", bound="CollectionBase")
TTo = TypeVar("TTo", bound="CollectionBase")


class CollectionBase(BaseModel, metaclass=CollectionMetaClass):
    _collection_name: ClassVar[str] = ""

    id: str | None = Field(None, alias="_id")
    key: str | None = Field(None, alias="_key")


class CollectionEdge(CollectionBase, Generic[TFrom, TTo]):
    """
    https://typing.python.org/en/latest/reference/generics.html
    https://pydantic.dev/docs/validation/latest/concepts/models/#generic-models
    """

    _graph_name: ClassVar[str] = ""

    id_from: str | None = Field(None, alias="_from")
    id_to: str | None = Field(None, alias="_to")

    vertex_from: TFrom = Field(exclude=True)
    vertex_to: TTo = Field(exclude=True)

    # @property
    # def vertex_from(self) -> TFrom | None:
    #     return self._vertex_from

    # @property
    # def vertex_to(self) -> TTo | None:
    #     return self._vertex_to

    @classmethod
    def get_edge_definition(cls) -> tuple[TFrom, TTo]:
        """
        get_original_bases: https://github.com/python/cpython/issues/122988#issuecomment-2287207096
        get_args: https://github.com/pydantic/pydantic/issues/7837#issuecomment-1772833646
        "Fail Fast" It's better to throw the exception than to handle the error and have strange behavior.
        """
        bases: tuple = get_original_bases(cls)
        collection_from, collection_to = get_args(bases[0])
        return collection_from, collection_to
