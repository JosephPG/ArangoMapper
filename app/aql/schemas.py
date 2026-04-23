from dataclasses import dataclass
from typing import Generic

from pydantic import BaseModel

from app.mapper.types import T, TEdge


@dataclass
class ForGraphData:
    collection: type[T]
    edge: type[TEdge]
    v_alias: str
    e_alias: str
    p_alias: str

    @property
    def graph_name(self) -> str:
        return self.edge._graph_name


class PathResponse(BaseModel, Generic[T, TEdge]):
    vertices: list[T] = []
    edges: list[TEdge] = []
    weights: list[int] = []


class GraphResponse(BaseModel, Generic[T, TEdge]):
    vertex: T | None = None
    edge: TEdge | None = None
    path: PathResponse[T, TEdge] | None = None
