import traceback

from arango.database import StandardDatabase, TransactionDatabase

from app.aql.aqlmanager import AQLManager
from app.aql.operator import For
from app.collections import Location, Route
from app.database.conn import execute_transaction
from app.database.manager import CollectionManager


def test_transaction(db: StandardDatabase):
    def function_for_transaction(txn: TransactionDatabase) -> Route:
        cm = CollectionManager(txn)
        first_location = Location(name="location A")
        second_location = Location(name="location B")

        cm.insert_many([first_location, second_location])
        cm.insert_graph(Route(vertex_from=first_location, vertex_to=second_location))

        return AQLManager(txn).add_for(For(Route)).first()

    collections = [Location._collection_name, Route._collection_name]

    res = execute_transaction(
        function_for_transaction, read=collections, write=collections
    )

    assert AQLManager(db).add_for(For(Route)).first().id == res.id


def test_transaction_error(db: StandardDatabase):
    def function_for_transaction(txn: TransactionDatabase) -> Location | None:
        cm = CollectionManager(txn)
        location = Location(name="location A")
        cm.insert(location)

        if 1 / 0:
            return location

    collections = [Location._collection_name]

    try:
        execute_transaction(function_for_transaction, read=collections, write=collections)
    except Exception:
        assert not AQLManager(db).add_for(For(Location)).first()
        assert traceback.format_exc()
