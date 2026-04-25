from typing import ClassVar

from app.mapper.base import CollectionBase, CollectionEdge


class Warehouse(CollectionBase):
    _collection_name: ClassVar[str] = "warehouses"

    name: str
    capacity: int


class Operator(CollectionBase):
    _collection_name: ClassVar[str] = "operators"

    nickname: str
    experience_years: int
    status: str


class Sensor(CollectionBase):
    _collection_name: ClassVar[str] = "sensors"

    model: str
    battery_level: int
    status: str


class Machine(CollectionBase):
    _collection_name: ClassVar[str] = "machines"

    serie: str
    year: int


class Manages(CollectionEdge[Warehouse, Operator]):
    """Edge: Warehouse -> Operator"""

    _collection_name: ClassVar[str] = "manages"
    _graph_name: ClassVar[str] = "managesgraph"

    shift: str


class Operates(CollectionEdge[Operator, Sensor]):
    """Edge: Operator -> Sensor"""

    _collection_name: ClassVar[str] = "operates"
    _graph_name: ClassVar[str] = "operatesgraph"

    last_maintenance: str
    is_primary: bool


class Link(CollectionEdge[Machine, Machine]):
    """Edge: Machine -> Machine"""

    _collection_name: ClassVar[str] = "links"
    _graph_name: ClassVar[str] = "linksgraph"

    last_maintenance: str
    is_primary: bool
