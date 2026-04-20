from arango.database import StandardDatabase

from app.collections import Device, Location, Route
from app.database.manager import CollectionManager
from app.mapper.expressions import FieldDescriptor


def test_model_not_instanced():
    assert isinstance(Location.id, FieldDescriptor)
    assert isinstance(Location.key, FieldDescriptor)
    assert isinstance(Location.name, FieldDescriptor)
    assert isinstance(Device.id, FieldDescriptor)
    assert isinstance(Device.key, FieldDescriptor)
    assert isinstance(Device.name, FieldDescriptor)
    assert isinstance(Device.type, FieldDescriptor)
    assert isinstance(Route.id, FieldDescriptor)
    assert isinstance(Route.key, FieldDescriptor)
    assert isinstance(Route.id_from, FieldDescriptor)
    assert isinstance(Route.id_to, FieldDescriptor)
    assert isinstance(Route.vertex_from, FieldDescriptor)
    assert isinstance(Route.vertex_to, FieldDescriptor)


def test_model_instanced(db: StandardDatabase):
    cm = CollectionManager(db)

    location = Location(name="nombre")

    assert not location.id
    assert not location.key
    assert location.name == "nombre"

    cm.insert(location)

    route = Route(vertex_from=location, vertex_to=location)

    assert isinstance(location.id, str)
    assert isinstance(location.key, str)
    assert location.name == "nombre"
    assert isinstance(route.vertex_from, Location)
    assert isinstance(route.vertex_to, Location)
