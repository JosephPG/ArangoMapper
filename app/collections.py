from typing import ClassVar

from app.mapper.base import CollectionBase, CollectionEdge


class Location(CollectionBase):
    _collection_name: ClassVar[str] = "locations"

    name: str


class Device(CollectionBase):
    _collection_name: ClassVar[str] = "devices"

    name: str
    type: str


class Route(CollectionEdge[Location, Location]):
    _collection_name: ClassVar[str] = "routes"
    _graph_name: ClassVar[str] = "routesgraph"


class Interconnection(CollectionEdge[Device, Device]):
    _collection_name: ClassVar[str] = "interconnections"
    _graph_name: ClassVar[str] = "interconnectionsgraph"

    type: str
