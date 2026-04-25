from typing import ClassVar

from app.mapper.base import CollectionBase, CollectionEdge


class Location(CollectionBase):
    _collection_name: ClassVar[str] = "locations"

    name: str


class Device(CollectionBase):
    _collection_name: ClassVar[str] = "devices"

    name: str
    type: str
    weight: int | None = None
    is_main: bool = True


class Owner(CollectionEdge[Location, Device]):
    _collection_name: ClassVar[str] = "owners"
    _graph_name: ClassVar[str] = "ownersgraph"

    year: int | None = None


class Route(CollectionEdge[Location, Location]):
    _collection_name: ClassVar[str] = "routes"
    _graph_name: ClassVar[str] = "routesgraph"


class Interconnection(CollectionEdge[Device, Device]):
    _collection_name: ClassVar[str] = "interconnections"
    _graph_name: ClassVar[str] = "interconnectionsgraph"

    type: str
