from arango.database import StandardDatabase

from app.collections import Location
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


def test_manager_update(db: StandardDatabase):
    cm = CollectionManager(db)

    location = Location(_key="1234", name="local A")
    cm.insert(location)

    location.name = "local changed"
    cm.update(location)

    assert location.id
    assert location.key == "1234"
    assert location.name == "local changed"


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
