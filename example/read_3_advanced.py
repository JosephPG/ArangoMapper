from arango.database import StandardDatabase
from loguru import logger

from app.aql.aqlmanager import AQLManager
from app.aql.operator import For, ForGraph, Let, Raw
from example.models import Manages, Operates, Operator, Sensor, Warehouse
from example.setup import setup


def complex_nested_clean(db: StandardDatabase):
    logger.info("\ncomplex_nested_clean (No Raw)")

    wh_madrid = AQLManager(db).get_by_id_or_key(Warehouse, "warehouses/wh1")

    # AQL equivalente generado automáticamente:
    # FOR v, e, p IN 1..1 OUTBOUND @start Manages
    #   FOR op_edge IN Operates
    #     FILTER op_edge._from == v._id
    #     FOR s IN sensors
    #       FILTER s._id == op_edge._to
    #       RETURN s

    data: list[Sensor] = (
        AQLManager(db)
        .add_for(ffg := ForGraph(wh_madrid, "OUTBOUND", Manages))
        .add_for(
            f_edge := For(Operates)
            # Comparamos el campo _from de la arista con el _id del vértice del grafo
            .filter(Operates.id_from == ffg.field(Operator.id))
        )
        .add_for(
            For(Sensor, alias="s")
            # Comparamos el _id del sensor con el _to de la arista Operates
            .filter(Sensor.id == f_edge.field(Operates.id_to))
            .filter(Sensor.status == "active")
        )
        # Retornamos directamente el modelo Sensor mapeado
        .list()
    )

    for s in data:
        logger.success(
            f"    Sensor: ID={s.id} Modelo={s.model} Batería={s.battery_level}%"
        )


def report_critical_sensors_by_operator(db: StandardDatabase):
    logger.info("\nreport_critical_sensors_by_operator")

    data = (
        AQLManager(db)
        .add_let(
            active_ops := Let(
                name="active_ops",
                value=For(Operator)
                .filter(Operator.status == "active")
                .subquery(Operator.id),
            )
        )
        .add_for(
            For(Operates, alias="ff")
            .filter(Operates.id_from.is_in(active_ops))
            .add_raw(
                Raw(
                    "LET s = DOCUMENT(ff._to) FILTER s.battery_level < 100",
                )
            )
            .add_raw(Raw("COLLECT op_id = ff._from WITH COUNT INTO total"))
        )
        .return_raw(Raw("{operator: op_id, critical_sensors: total}"))
        .list()
    )

    for x in data:
        logger.success(
            f"    Operator: {x['operator']} | Sensores Críticos: {x['critical_sensors']}"
        )


def complex_nested_example(db: StandardDatabase):
    logger.info("\ncomplex_nested_example (Graph + Nested FORs)")

    wh_madrid = AQLManager(db).get_by_id_or_key(Warehouse, "warehouses/wh1")

    # AQL Resultante esperado:
    # FOR v, e, p IN 1..1 OUTBOUND @start Manages  <-- ForGraph
    #   FOR op_edge IN Operates                    <-- FOR anidado 1
    #     FILTER op_edge._from == v._id
    #     FOR s IN sensors                         <-- FOR anidado 2
    #       FILTER s._id == op_edge._to AND s.status == "active"
    #       RETURN ...

    data = (
        AQLManager(db)
        .add_for(ForGraph(wh_madrid, "OUTBOUND", Manages, v_alias="operator_v"))
        .add_for(
            For(Operates, alias="op_edge").filter(Raw("op_edge._from == operator_v._id"))
        )
        .add_for(
            For(Sensor, alias="s")
            .filter(Raw("s._id == op_edge._to"))
            .filter(Sensor.status == "active")
        )
        .return_raw(
            Raw(
                "{ operator: operator_v.nickname, sensor: s.model, battery: s.battery_level }"
            )
        )
        .list()
    )

    for x in data:
        logger.success(
            f"    Op: {x['operator']} -> Sensor: {x['sensor']} ({x['battery']}%)"
        )


def subquery_graph_filter(db: StandardDatabase):
    logger.info("\nsubquery_graph_filter (Add_raw for nested subquery)")

    wh_madrid = AQLManager(db).get_by_id_or_key(Warehouse, "warehouses/wh1")

    # Usamos add_raw para el segundo FOR dentro de la subconsulta del Let
    data: list[Sensor] = (
        AQLManager(db)
        .add_let(
            sensors_in_madrid := Let(
                name="sensors_madrid",
                value=ForGraph(wh_madrid, "OUTBOUND", Manages, v_alias="v")
                .add_raw(Raw("FOR op IN operates FILTER op._from == v._id"))
                .subquery_raw(Raw("op._to")),
            )
        )
        .add_for(fs := For(Sensor).filter(Sensor.id.is_in(sensors_in_madrid)))
        .add_sort(fs.field(Sensor.battery_level), order="desc")
        .list()
    )

    for s in data:
        logger.success(f"    Sensor en Madrid: {s.model} | Batería: {s.battery_level}%")


if __name__ == "__main__":
    with setup() as db:
        complex_nested_clean(db)
        report_critical_sensors_by_operator(db)
        complex_nested_example(db)
        subquery_graph_filter(db)
