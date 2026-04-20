from arango.database import StandardDatabase

from app.collections import Device, Interconnection, Location, Route
from app.database.migrate import sync_migration

from tests.utils import delete_all_in_db


def test_sync_migrate(db: StandardDatabase):
    delete_all_in_db(db)

    sync_migration(db)

    assert db.has_graph(Route._graph_name)
    assert db.has_graph(Interconnection._graph_name)
    assert db.has_collection(Location._collection_name)
    assert db.has_collection(Device._collection_name)
    assert db.has_collection(Route._collection_name)
    assert db.has_collection(Interconnection._collection_name)
