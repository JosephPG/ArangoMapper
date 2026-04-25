from arango.database import StandardDatabase

from app.aql.aqlmanager import AQLManager
from app.aql.operator import For, ForGraph, Let
from app.aql.schemas import GraphResponse
from app.database.conn import get_db
from example import setup
from example.models import Link, Machine, Manages, Operates, Operator, Sensor, Warehouse


def get_by_id(db: StandardDatabase):
    wh: Warehouse = AQLManager(db).get_by_id_or_key(Warehouse, "warehouses/wh1")

    print(f"get_by_id: Warehouse id={wh.id} name={wh.name}")


def get_by_key(db: StandardDatabase):
    mn: Manages = AQLManager(db).get_by_id_or_key(Manages, "mn1")

    print(
        f"\nget_by_key: Manage id='{mn.id}' shift='{mn.shift}' "
        + f"warhouse='{mn.vertex_from.name}' operator='{mn.vertex_to.nickname}'"
    )


def for_simple_collection(db: StandardDatabase):
    print("\nfor_simple_collection:")

    sensors: list[Sensor] = AQLManager(db).add_for(For(Sensor)).list()

    for x in sensors:
        print(
            f"    model='{x.model}' battery_level='{x.battery_level}' status='{x.status}'"
        )


def for_simple_edge(db: StandardDatabase):
    print("\nfor_simple_edge:")

    data: list[Operates] = AQLManager(db).add_for(For(Operates)).list()

    for x in data:
        print(
            f"    last_maintenance='{x.last_maintenance}' is_primary={x.is_primary} "
            + f"operator='{x.vertex_from.nickname}' sensor='{x.vertex_to.model}'"
        )


def for_with_filter(db: StandardDatabase):
    print("\nfor_with_filter:")

    data: list[Sensor] = (
        AQLManager(db)
        .add_for(
            For(Sensor)
            .filter(
                ((Sensor.battery_level >= 40) & (Sensor.battery_level < 95))
                | (Sensor.status == "inactive")
            )
            .filter((Sensor.model.is_not_null()))
        )
        .list()
    )

    for x in data:
        print(
            f"    model='{x.model}' battery_level='{x.battery_level}' status='{x.status}' "
        )


def for_graph(db: StandardDatabase):
    print("\nfor_graph:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    ops: list[GraphResponse] = (
        AQLManager(db).add_for(ForGraph(operator, "OUTBOUND", Operates)).list()
    )

    for x in ops:
        print(
            f"    last_maintenance='{x.edge.last_maintenance}' is_primary={x.edge.is_primary} "
            + f"vertex='{x.vertex.model}' path.vertices_len={len(x.path.vertices)} "
            + f"path.edges_len={len(x.path.edges)} weights={x.path.weights}"
        )


def for_graph_with_depth(db: StandardDatabase):
    print("\nfor_graph_depth:")

    machine: Machine = AQLManager(db).get_by_id_or_key(Machine, "mc1")

    ops: list[GraphResponse] = (
        AQLManager(db)
        .add_for(ForGraph(machine, "OUTBOUND", Link, min_d=1, max_d=3))
        .list()
    )

    for x in ops:
        print(
            f"    last_maintenance='{x.edge.last_maintenance}' is_primary={x.edge.is_primary} "
            + f"vertex='{x.vertex.serie}' path.vertices_len={len(x.path.vertices)} "
            + f"path.edges_len={len(x.path.edges)} weights={x.path.weights}"
        )


def for_graph_with_filter(db: StandardDatabase):
    print("\nfor_graph_filter:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    ops: list[GraphResponse] = (
        AQLManager(db)
        .add_for(
            ForGraph(operator, "OUTBOUND", Operates)
            .filter((Sensor.model == "v2") & (Operates.is_primary.is_false()))
            .filter(Operates.last_maintenance.is_not_null())
        )
        .list()
    )

    for x in ops:
        print(
            f"    last_maintenance='{x.edge.last_maintenance}' is_primary={x.edge.is_primary} "
            + f"vertex='{x.vertex.model}' path.vertices_len={len(x.path.vertices)} "
            + f"path.edges_len={len(x.path.edges)} weights={x.path.weights}"
        )


def for_with_limit(db: StandardDatabase):
    print("\nfor_with_limit:")

    data: list[Operates] = AQLManager(db).add_for(For(Operates)).limit(count=2).list()

    for x in data:
        print(
            f"    last_maintenance='{x.last_maintenance}' is_primary={x.is_primary} "
            + f"operator='{x.vertex_from.nickname}' sensor='{x.vertex_to.model}'"
        )


def for_graph_with_limit(db: StandardDatabase):
    print("\nfor_graph_with_limit:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    ops: list[GraphResponse] = (
        AQLManager(db)
        .add_for(ForGraph(operator, "OUTBOUND", Operates))
        .limit(count=1, offset=1)
        .list()
    )

    for x in ops:
        print(
            f"    last_maintenance='{x.edge.last_maintenance}' is_primary={x.edge.is_primary} "
            + f"vertex='{x.vertex.model}' path.vertices_len={len(x.path.vertices)} "
            + f"path.edges_len={len(x.path.edges)} weights={x.path.weights}"
        )


def for_with_sort(db: StandardDatabase):
    print("\nfor_with_sort:")

    data: list[Operates] = (
        AQLManager(db)
        .add_for(ff := For(Operates))
        .add_sort(ff.field(Operates.last_maintenance))
        .add_sort(ff.field(Operates.is_primary), order="desc")
        .list()
    )

    for x in data:
        print(
            f"    last_maintenance='{x.last_maintenance}' is_primary={x.is_primary} "
            + f"operator='{x.vertex_from.nickname}' sensor='{x.vertex_to.model}'"
        )


def for_graph_with_sort(db: StandardDatabase):
    print("\nfor_graph_with_limit:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    ops: list[GraphResponse] = (
        AQLManager(db)
        .add_for(ffg := ForGraph(operator, "OUTBOUND", Operates))
        .add_sort(ffg.field(Sensor.model), order="desc")
        .add_sort(ffg.field(Operates.last_maintenance))
        .list()
    )

    for x in ops:
        print(
            f"    last_maintenance='{x.edge.last_maintenance}' is_primary={x.edge.is_primary} "
            + f"vertex='{x.vertex.model}' path.vertices_len={len(x.path.vertices)} "
            + f"path.edges_len={len(x.path.edges)} weights={x.path.weights}"
        )


def for_count(db: StandardDatabase):
    print("\nfor_count:")

    data: int = AQLManager(db).add_for(For(Operates)).count()

    print(f"    Total operates: {data}")


def for_first(db: StandardDatabase):
    print("\nfor_first:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    gp: GraphResponse = (
        AQLManager(db).add_for(ForGraph(operator, "OUTBOUND", Operates)).first()
    )

    print(
        f"    last_maintenance='{gp.edge.last_maintenance}' is_primary={gp.edge.is_primary} "
        + f"vertex='{gp.vertex.model}' path.vertices_len={len(gp.path.vertices)} "
        + f"path.edges_len={len(gp.path.edges)} weights={gp.path.weights}"
    )


def for_last(db: StandardDatabase):
    print("\nfor_last:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    gp: GraphResponse = (
        AQLManager(db).add_for(ForGraph(operator, "OUTBOUND", Operates)).last()
    )

    print(
        f"    last_maintenance='{gp.edge.last_maintenance}' is_primary={gp.edge.is_primary} "
        + f"vertex='{gp.vertex.model}' path.vertices_len={len(gp.path.vertices)} "
        + f"path.edges_len={len(gp.path.edges)} weights={gp.path.weights}"
    )


def let_with_for(db: StandardDatabase):
    print("\nlet_with_for:")

    data: list[Operates] = (
        AQLManager(db)
        .add_let(
            fl := Let(
                name="variable",
                value=For(Operator)
                .filter(Operator.nickname == "Pedro")
                .subquery(Operator.id),
            )
        )
        .add_for(For(Operates).filter(Operates.id_from.is_in(fl)))
        .list()
    )

    for x in data:
        print(
            f"    last_maintenance='{x.last_maintenance}' is_primary={x.is_primary} "
            + f"operator='{x.vertex_from.nickname}' sensor='{x.vertex_to.model}'"
        )


def let_with_for_graph(db: StandardDatabase):
    print("\nlet_with_for_graph:")

    wh_madrid: Warehouse = AQLManager(db).get_by_id_or_key(Warehouse, "warehouses/wh1")

    data: list[Operates] = (
        AQLManager(db)
        .add_let(
            ops_madrid := Let(
                name="ops_madrid",
                value=ForGraph(wh_madrid, "OUTBOUND", Manages).subquery(Operator.id),
            )
        )
        .add_for(For(Operates).filter(Operates.id_from.is_in(ops_madrid)))
        .list()
    )

    for x in data:
        print(
            f"    last_maintenance='{x.last_maintenance}' is_primary={x.is_primary} "
            + f"operator='{x.vertex_from.nickname}' sensor='{x.vertex_to.model}'"
        )


if __name__ == "__main__":
    db: StandardDatabase = get_db()

    try:
        setup.dummy_data(db)
        get_by_id(db)
        get_by_key(db)
        for_simple_collection(db)
        for_simple_edge(db)
        for_with_filter(db)
        for_graph(db)
        for_graph_with_depth(db)
        for_graph_with_filter(db)
        for_with_limit(db)
        for_graph_with_limit(db)
        for_with_sort(db)
        for_graph_with_sort(db)
        for_count(db)
        for_first(db)
        for_last(db)
        let_with_for(db)
        let_with_for_graph(db)
    except:
        raise
    finally:
        setup.truncate(db)
