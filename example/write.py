from arango.database import StandardDatabase
from loguru import logger

from app.aql.aqlmanager import AQLManager
from app.aql.operator import For
from app.database.manager import CollectionManager
from example.models import Manages, Operator, Warehouse
from example.setup import setup


def insert(db: StandardDatabase):
    logger.info("\ninsert")

    cm: CollectionManager = CollectionManager(db)

    warehouse: Warehouse = Warehouse(name="Perù", capacity=100)

    cm.insert(warehouse)

    logger.success(
        f"    Warehouse id='{warehouse.id}' key='{warehouse.id}' name='{warehouse.name}'"
    )


def insert_graph(db: StandardDatabase):
    logger.info("\ninsert_graph")

    cm = CollectionManager(db)

    warehouse: Warehouse = Warehouse(name="Perù", capacity=100)
    operator: Operator = Operator(nickname="Allen", experience_years=2, status="active")

    cm.insert(warehouse)
    cm.insert(operator)

    manage: Manages = Manages(vertex_from=warehouse, vertex_to=operator, shift="day")

    cm.insert_graph(manage)

    logger.success(
        f"    Manage id='{manage.id}' key='{manage.id}' key='{manage.shift}' "
        + f"warehouse='{manage.vertex_from.name}' operator='{manage.vertex_to.nickname}'"
    )


def update(db: StandardDatabase):
    logger.info("\nupdate")

    cm: CollectionManager = CollectionManager(db)

    warehouse = Warehouse(name="Perù", capacity=100)

    cm.insert(warehouse)

    logger.info(
        f"    Warehouse id='{warehouse.id}' name='{warehouse.name}' capacity='{warehouse.capacity}'"
    )

    warehouse.capacity = 50

    cm.update(warehouse)

    logger.success(
        f"    Warehouse id='{warehouse.id}' name='{warehouse.name}' capacity='{warehouse.capacity}'"
    )


def update_graph(db: StandardDatabase):
    logger.info("\nupdate_graph")

    cm = CollectionManager(db)

    warehouse: Warehouse = Warehouse(name="Perù", capacity=100)
    operator: Operator = Operator(nickname="Allen", experience_years=2, status="active")

    cm.insert(warehouse)
    cm.insert(operator)

    manage: Manages = Manages(vertex_from=warehouse, vertex_to=operator, shift="day")

    cm.insert_graph(manage)

    logger.success(
        f"    Manage id='{manage.id}' key='{manage.id}' shift='{manage.shift}' "
        + f"warehouse='{warehouse.name}' operator='{operator.nickname}'"
    )

    manage.shift = "night"

    cm.update(manage)

    logger.success(
        f"    Manage id='{manage.id}' key='{manage.id}' shift='{manage.shift}' "
        + f"warehouse='{manage.vertex_from.name}' operator='{manage.vertex_to.nickname}'"
    )


def delete(db: StandardDatabase):
    logger.info("\ndelete")

    cm = CollectionManager(db)

    warehouse: Warehouse = Warehouse(_key="texas1", name="Texas", capacity=100)

    cm.insert(warehouse)

    logger.info(
        f"    Warehouse id='{warehouse.id}' key='{warehouse.id}' name='{warehouse.name}'"
    )

    cm.delete(warehouse)

    logger.success("    " + str(AQLManager(db).get_by_id_or_key(Warehouse, "texas1")))


def delete_graph(db: StandardDatabase):
    logger.info("\ndelete_graph")

    cm = CollectionManager(db)

    warehouse: Warehouse = Warehouse(name="Perù", capacity=100)
    operator: Operator = Operator(nickname="Allen", experience_years=2, status="active")

    cm.insert(warehouse)
    cm.insert(operator)

    manage: Manages = Manages(
        _key="manage1", vertex_from=warehouse, vertex_to=operator, shift="day"
    )

    cm.insert_graph(manage)

    logger.info(
        f"    Manage id='{manage.id}' key='{manage.id}' key='{manage.shift}' "
        + f"warehouse='{manage.vertex_from.name}' operator='{manage.vertex_to.nickname}'"
    )

    cm.delete(manage)

    logger.success("    " + str(AQLManager(db).get_by_id_or_key(Manages, "manage1")))


def insert_many(db: StandardDatabase):
    logger.info("\ninsert_many")

    cm: CollectionManager = CollectionManager(db)

    warehouses: list[Warehouse] = [
        Warehouse(name="Texas", capacity=100),
        Warehouse(name="Lima", capacity=10),
    ]

    cm.insert_many(warehouses)

    for x in warehouses:
        logger.success(f"    Warehouse id='{x.id}' key='{x.id}' name='{x.name}'")


def insert_many_graph(db: StandardDatabase):
    logger.info("\ninsert_many_graph")

    cm: CollectionManager = CollectionManager(db)

    warehouse: Warehouse = Warehouse(name="Perù", capacity=100)
    operator1: Operator = Operator(nickname="Allen", experience_years=2, status="active")
    operator2: Operator = Operator(nickname="Pascal", experience_years=2, status="active")

    cm.insert(warehouse)
    cm.insert(operator1)
    cm.insert(operator2)

    manages = [
        Manages(vertex_from=warehouse, vertex_to=operator1, shift="day"),
        Manages(vertex_from=warehouse, vertex_to=operator2, shift="day"),
    ]

    cm.insert_many(manages)

    for x in manages:
        logger.success(
            f"    Manage id='{x.id}' key='{x.id}' key='{x.shift}' "
            + f"warehouse='{x.vertex_from.name}' operator='{x.vertex_to.nickname}'"
        )


def delete_many(db: StandardDatabase):
    logger.info("\ndelete_many")

    cm: CollectionManager = CollectionManager(db)

    warehouses: list[Warehouse] = [
        Warehouse(name="Texas", capacity=100),
        Warehouse(name="Lima", capacity=10),
    ]

    cm.insert_many(warehouses)

    for x in warehouses:
        logger.info(f"    Warehouse id='{x.id}' key='{x.id}' name='{x.name}'")

    cm.delete_many(warehouses)

    founded: int = (
        AQLManager(db)
        .add_for(For(Manages).filter(Manages.key.is_in([x.key for x in warehouses])))
        .count()
    )

    logger.success("    Warehouse founded: " + str(founded))


def delete_many_graph(db: StandardDatabase):
    logger.info("\ndelete_many_graph")

    cm: CollectionManager = CollectionManager(db)

    warehouse: Warehouse = Warehouse(name="Perù", capacity=100)
    operator1: Operator = Operator(nickname="Allen", experience_years=2, status="active")
    operator2: Operator = Operator(nickname="Pascal", experience_years=2, status="active")

    cm.insert(warehouse)
    cm.insert(operator1)
    cm.insert(operator2)

    manages = [
        Manages(_key="mngs1", vertex_from=warehouse, vertex_to=operator1, shift="day"),
        Manages(_key="mngs2", vertex_from=warehouse, vertex_to=operator2, shift="day"),
    ]

    cm.insert_many(manages)

    for x in manages:
        logger.info(
            f"    Manage id='{x.id}' key='{x.id}' key='{x.shift}' "
            + f"warehouse='{x.vertex_from.name}' operator='{x.vertex_to.nickname}'"
        )

    cm.delete_many(manages)

    founded: int = (
        AQLManager(db)
        .add_for(For(Manages).filter(Manages.key.is_in([x.key for x in manages])))
        .count()
    )

    logger.success("    Manages founded: " + str(founded))


if __name__ == "__main__":
    with setup() as db:
        insert(db)
        insert_graph(db)
        update(db)
        update_graph(db)
        delete(db)
        delete_graph(db)
        insert_many(db)
        insert_many_graph(db)
        delete_many(db)
        delete_many_graph(db)
