from typing import Generic, TypeVar

from pydantic import BaseModel

from app.mapper.base import CollectionBase, CollectionEdge

T = TypeVar("T", bound=CollectionBase)
TEdge = TypeVar("TEdge", bound=CollectionEdge)


class PathResponse(BaseModel, Generic[T, TEdge]):
    vertices: list[T] = []
    edges: list[TEdge] = []
    weights: list[int] = []


class GraphResponse(BaseModel, Generic[T, TEdge]):
    vertex: T | None = None
    edge: TEdge | None = None
    path: PathResponse[T, TEdge] | None = None
