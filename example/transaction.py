from arango.database import StandardDatabase, TransactionDatabase
from loguru import logger

from app.aql.aqlmanager import AQLManager
from app.database.conn import execute_transaction, get_db
from app.database.manager import CollectionManager
from example import setup
from example.models import Manages, Operator, Warehouse


def transaction_example(db: StandardDatabase):
    logger.info("\ntransaction_example")

    def function_for_transaction(txn: TransactionDatabase) -> any:
        cm = CollectionManager(txn)

        warehouse: Warehouse = Warehouse(name="Perù", capacity=100)
        operator: Operator = Operator(
            nickname="Allen", experience_years=2, status="active"
        )

        cm.insert(warehouse)
        cm.insert(operator)

        manage: Manages = Manages(vertex_from=warehouse, vertex_to=operator, shift="day")

        cm.insert_graph(manage)

        return manage.id

    collections = [
        Warehouse._collection_name,
        Operator._collection_name,
        Manages._collection_name,
    ]

    res: str = execute_transaction(
        function_for_transaction, read=collections, write=collections
    )

    manage: Manages = AQLManager(db).get_by_id_or_key(Manages, res)

    logger.success(
        f"    id='{manage.id}' shift={manage.shift} "
        + f"warehouse='{manage.vertex_from.name}' operatorr='{manage.vertex_to.nickname}'"
    )


if __name__ == "__main__":
    db: StandardDatabase = get_db()

    try:
        setup.dummy_data(db)
        transaction_example(db)
    except:
        raise
    finally:
        setup.truncate(db)
