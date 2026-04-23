from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from app.mapper.base import CollectionBase, CollectionEdge

T = TypeVar("T", bound="CollectionBase")
TEdge = TypeVar("TEdge", bound="CollectionEdge")
