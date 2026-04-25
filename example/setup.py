import sys
from contextlib import contextmanager

from arango.database import StandardDatabase
from loguru import logger

from app.database.conn import get_db
from app.database.manager import CollectionManager
from example.models import Link, Machine, Manages, Operates, Operator, Sensor, Warehouse

logger.remove()
logger.add(sys.stdout, format="<level>{message}</level>")


def dummy_data(db: StandardDatabase):
    for x in [Warehouse, Operator, Sensor, Machine]:
        if not db.has_collection(x._collection_name):
            db.create_collection(x._collection_name)

    if not db.has_graph(Manages._graph_name):
        graph = db.create_graph(Manages._graph_name)
        graph.create_edge_definition(
            edge_collection=Manages._collection_name,
            from_vertex_collections=[Warehouse._collection_name],
            to_vertex_collections=[Operator._collection_name],
        )

    if not db.has_graph(Operates._graph_name):
        graph = db.create_graph(Operates._graph_name)
        graph.create_edge_definition(
            edge_collection=Operates._collection_name,
            from_vertex_collections=[Operator._collection_name],
            to_vertex_collections=[Sensor._collection_name],
        )

    if not db.has_graph(Link._graph_name):
        graph = db.create_graph(Link._graph_name)
        graph.create_edge_definition(
            edge_collection=Link._collection_name,
            from_vertex_collections=[Machine._collection_name],
            to_vertex_collections=[Machine._collection_name],
        )

    cm: CollectionManager = CollectionManager(db)

    wh_madrid = Warehouse(_id="warehouses/wh1", name="Madrid Central", capacity=1000)
    wh_bcn = Warehouse(_id="warehouses/wh2", name="Barcelona Hub", capacity=500)

    cm.insert_many([wh_madrid, wh_bcn])

    op_pedro = Operator(
        _id="operators/opp", nickname="Pedro", experience_years=12, status="active"
    )
    op_marta = Operator(
        _id="operators/opm", nickname="Marta", experience_years=8, status="active"
    )
    op_lucia = Operator(
        _id="operators/opl", nickname="Lucia", experience_years=3, status="on_leave"
    )

    cm.insert_many([op_pedro, op_marta, op_lucia])

    s1 = Sensor(_id="sensors/sn1", model="v1", battery_level=5, status="active")
    s2 = Sensor(_id="sensors/sn2", model="v1", battery_level=45, status="active")
    s3 = Sensor(_id="sensors/sn3", model="v2", battery_level=90, status="active")
    s4 = Sensor(_id="sensors/sn4", model="v1", battery_level=12, status="active")
    s5 = Sensor(_id="sensors/sn5", model="v2", battery_level=100, status="inactive")

    cm.insert_many([s1, s2, s3, s4, s5])

    mchn1 = Machine(_id="machines/mc1", serie="s11", year=5)
    mchn2 = Machine(_id="machines/mc2", serie="s12", year=10)
    mchn3 = Machine(_id="machines/mc3", serie="s13", year=8)
    mchn4 = Machine(_id="machines/mc4", serie="s14", year=20)
    mchn5 = Machine(_id="machines/mc5", serie="s15", year=3)
    mchn6 = Machine(_id="machines/mc6", serie="s16", year=10)

    cm.insert_many([mchn1, mchn2, mchn3, mchn4, mchn5, mchn6])

    cm.insert_many(
        [
            Manages(_key="mn1", vertex_from=wh_madrid, vertex_to=op_pedro, shift="day"),
            Manages(_key="mn2", vertex_from=wh_madrid, vertex_to=op_marta, shift="night"),
            Manages(_key="mn3", vertex_from=wh_bcn, vertex_to=op_lucia, shift="day"),
        ]
    )

    cm.insert_many(
        [
            Operates(
                vertex_from=op_pedro,
                vertex_to=s1,
                is_primary=True,
                last_maintenance="2023-01-01",
            ),
            Operates(
                vertex_from=op_pedro,
                vertex_to=s3,
                is_primary=False,
                last_maintenance="2023-05-10",
            ),
            Operates(
                vertex_from=op_marta,
                vertex_to=s4,
                is_primary=True,
                last_maintenance="2023-06-15",
            ),
            Operates(
                vertex_from=op_lucia,
                vertex_to=s2,
                is_primary=True,
                last_maintenance="2023-02-20",
            ),
        ]
    )

    cm.insert_many(
        [
            Link(
                vertex_from=mchn1,
                vertex_to=mchn2,
                is_primary=True,
                last_maintenance="2023-01-01",
            ),
            Link(
                vertex_from=mchn2,
                vertex_to=mchn3,
                is_primary=False,
                last_maintenance="2023-05-10",
            ),
            Link(
                vertex_from=mchn3,
                vertex_to=mchn4,
                is_primary=True,
                last_maintenance="2023-06-15",
            ),
            Link(
                vertex_from=mchn4,
                vertex_to=mchn5,
                is_primary=True,
                last_maintenance="2023-02-20",
            ),
            Link(
                vertex_from=mchn5,
                vertex_to=mchn6,
                is_primary=True,
                last_maintenance="2023-02-20",
            ),
        ]
    )

    logger.info("=====================DUMMY DATA LOADED=====================")


def truncate(db: StandardDatabase):
    for x in [Manages, Operates, Operator, Sensor, Warehouse, Machine, Link]:
        db.collection(x._collection_name).truncate()

    logger.info("\n=====================DUMMY DATA TRUNCATE=====================")


@contextmanager
def setup():
    try:
        db: StandardDatabase = get_db()
        dummy_data(db)
        yield db
    except:
        raise
    finally:
        truncate(db)
