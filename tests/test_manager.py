from arango.database import StandardDatabase

from app.aql.aqlmanager import AQLManager
from app.collections import Device, Interconnection, Location, Route
from app.database.manager import CollectionManager


def test_manager_insert_not_id_and_key(db: StandardDatabase):
    cm = CollectionManager(db)

    location = Location(name="local A")
    cm.insert(location)

    assert location.id
    assert location.key
    assert location.name == "local A"


def test_manager_insert_with_id_and_key(db: StandardDatabase):
    cm = CollectionManager(db)

    location = Location(_id="locations/1234", _key="1234", name="local A")
    cm.insert(location)

    assert location.id == "locations/1234"
    assert location.key == "1234"
    assert location.name == "local A"


def test_manager_insert_graph(db: StandardDatabase):
    cm = CollectionManager(db)

    first_location = Location(name="local A")
    cm.insert(first_location)

    second_location = Location(name="local B")
    cm.insert(second_location)

    route = Route(vertex_from=first_location, vertex_to=second_location)
    cm.insert_graph(route)

    assert route.id
    assert route.key
    assert route.vertex_from.id
    assert route.vertex_from.name == "local A"
    assert route.vertex_to.id
    assert route.vertex_to.name == "local B"


def test_manager_update(db: StandardDatabase):
    cm = CollectionManager(db)

    location = Location(_key="1234", name="local A")
    cm.insert(location)

    location.name = "local changed"
    cm.update(location)

    assert location.id
    assert location.key == "1234"
    assert location.name == "local changed"


def test_manager_update_graph(db: StandardDatabase):
    cm = CollectionManager(db)

    first_device = Device(name="device A", type="engine")
    cm.insert(first_device)

    second_device = Device(name="device B", type="engine")
    cm.insert(second_device)

    interconnection = Interconnection(
        _key="1234", vertex_from=first_device, vertex_to=second_device, type="wire"
    )
    cm.insert_graph(interconnection)

    assert interconnection.type == "wire"

    interconnection.type = "antenna"

    cm.update(interconnection)

    assert interconnection.id
    assert interconnection.key == "1234"
    assert interconnection.type == "antenna"


def test_manager_insert_many(db: StandardDatabase):
    cm = CollectionManager(db)

    locations = [
        Location(name="local A"),
        Location(name="local B"),
        Location(name="local C"),
        Location(name="local D"),
        Location(name="local E"),
    ]

    cm.insert_many(locations)

    expected_names = ["local A", "local B", "local C", "local D", "local E"]

    for location, name in zip(locations, expected_names):
        assert location.id
        assert location.key
        assert location.name == name


def test_manager_insert_many_graph(db: StandardDatabase):
    cm = CollectionManager(db)

    locations = [
        Location(name="local A"),
        Location(name="local B"),
        Location(name="local C"),
        Location(name="local D"),
        Location(name="local E"),
        Location(name="local F"),
    ]
    cm.insert_many(locations)

    routes = [
        Route(vertex_from=locations[0], vertex_to=locations[1]),
        Route(vertex_from=locations[2], vertex_to=locations[3]),
        Route(vertex_from=locations[4], vertex_to=locations[5]),
    ]
    cm.insert_many(routes)

    for route in routes:
        assert route.id
        assert route.key
        assert route.id_from
        assert route.id_to


def test_manager_delete(db: StandardDatabase):
    cm = CollectionManager(db)

    location = Location(_id="locations/1234", _key="1234", name="local A")
    cm.insert(location)

    assert AQLManager(db).get_by_id_or_key(Location, "1234")

    cm.delete(location)

    assert not AQLManager(db).get_by_id_or_key(Location, "1234")
