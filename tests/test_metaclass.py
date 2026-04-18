from arango.database import StandardDatabase

from app.collections import Device, Location, Route
from app.database.manager import CollectionManager


def test_model_not_instanced():
    assert Location.id.target == "_id"
    assert Location.key.target == "_key"
    assert Location.name.target == "name"
    assert Device.id.target == "_id"
    assert Device.key.target == "_key"
    assert Device.name.target == "name"
    assert Device.type.target == "type"
    assert Route.id.target == "_id"
    assert Route.key.target == "_key"
    assert Route.id_from.target == "_from"
    assert Route.id_to.target == "_to"
    assert Route.vertex_from.target == "vertex_from"
    assert Route.vertex_to.target == "vertex_to"


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
