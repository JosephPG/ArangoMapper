from arango.database import StandardDatabase

from app.collections import Location
from app.database.manager import CollectionManager


def test_manage_insert_not_id_and_key(db: StandardDatabase):
    collection_manager = CollectionManager(db)

    location = Location(name="local A")
    collection_manager.insert(location)

    assert location.id
    assert location.key
    assert location.name == "local A"


def test_manage_insert_with_id_and_key(db: StandardDatabase):
    collection_manager = CollectionManager(db)

    location = Location(_id="locations/1234", _key="1234", name="local A")
    collection_manager.insert(location)

    assert location.id == "locations/1234"
    assert location.key == "1234"
    assert location.name == "local A"
