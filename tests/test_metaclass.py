from arango.database import StandardDatabase

from app.collections import Device, Location, Route
from app.database.manager import CollectionManager


def test_model_not_instanced():
    assert Location.id == "_id"
    assert Location.key == "_key"
    assert Location.name == "name"
    assert Device.id == "_id"
    assert Device.key == "_key"
    assert Device.name == "name"
    assert Device.type == "type"
    assert Route.id == "_id"
    assert Route.key == "_key"
    assert Route.id_from == "_from"
    assert Route.id_to == "_to"


def test_model_instanced(db: StandardDatabase):
    cm = CollectionManager(db)

    location = Location(name="nombre")

    assert not location.id
    assert not location.key
    assert location.name == "nombre"

    cm.insert(location)

    assert location.id and location.id != "_id"
    assert location.key and location.key != "_key"
    assert location.name == "nombre"
