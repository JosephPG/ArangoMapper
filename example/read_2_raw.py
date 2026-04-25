from arango.database import StandardDatabase
from loguru import logger

from app.aql.aqlmanager import AQLManager
from app.aql.operator import For, ForGraph, Let, Raw
from app.aql.schemas import GraphResponse
from example.models import Operates, Operator, Sensor
from example.setup import setup


def raw(db: StandardDatabase):
    logger.info("raw:")
    data: list = (
        AQLManager(db)
        .add_raw(
            Raw(
                "FOR x IN sensors FILTER x.status == @value RETURN x",
                bind_vars={"value": "active"},
            )
        )
        .list()
    )

    for x in data:
        logger.success(f"    {x}")


def raw_in_let(db: StandardDatabase):
    logger.info("\nraw_in_let:")
    data: list[Operates] = (
        AQLManager(db)
        .add_let(
            fl := Let(
                name="variable",
                value=Raw("@values", bind_vars={"values": ["operators/opp"]}),
            )
        )
        .add_for(For(Operates).filter(Operates.id_from.is_in(fl)))
        .list()
    )

    for x in data:
        logger.success(
            f"    last_maintenance='{x.last_maintenance}' is_primary={x.is_primary} "
            + f"operator='{x.vertex_from.nickname}' sensor='{x.vertex_to.model}'"
        )


def raw_how_value_in_filter(db: StandardDatabase):
    logger.info("\nraw_how_value_in_filter:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    ops: list[GraphResponse] = (
        AQLManager(db)
        .add_for(
            ForGraph(operator, "OUTBOUND", Operates)
            .filter((Sensor.model == "v2") & (Operates.is_primary.is_false()))
            .filter(Operates.last_maintenance != Raw("@value", bind_vars={"value": None}))
        )
        .list()
    )

    for x in ops:
        logger.success(
            f"    last_maintenance='{x.edge.last_maintenance}' is_primary={x.edge.is_primary} "
            + f"vertex='{x.vertex.model}' path.vertices_len={len(x.path.vertices)} "
            + f"path.edges_len={len(x.path.edges)} weights={x.path.weights}"
        )


def raw_in_filter(db: StandardDatabase):
    logger.info("\nraw_in_filter:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    ops: list[GraphResponse] = (
        AQLManager(db)
        .add_for(
            ForGraph(operator, "OUTBOUND", Operates, v_alias="v", e_alias="e")
            .filter(
                Raw("v.model == @value", bind_vars={"value": "v2"})
                & (Operates.is_primary.is_false())
            )
            .filter(Raw("e.last_maintenance != @value", bind_vars={"value": None}))
        )
        .list()
    )

    for x in ops:
        logger.success(
            f"    last_maintenance='{x.edge.last_maintenance}' is_primary={x.edge.is_primary} "
            + f"vertex='{x.vertex.model}' path.vertices_len={len(x.path.vertices)} "
            + f"path.edges_len={len(x.path.edges)} weights={x.path.weights}"
        )


def raw_inside_for(db: StandardDatabase):
    logger.info("\nraw_inside_filter:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    ops: list[GraphResponse] = (
        AQLManager(db)
        .add_for(
            ForGraph(
                operator, "OUTBOUND", Operates, v_alias="v", e_alias="e", p_alias="p"
            ).add_raw(Raw("SORT LENGTH(p.vertices)"))
        )
        .list()
    )

    for x in ops:
        logger.success(
            f"    last_maintenance='{x.edge.last_maintenance}' is_primary={x.edge.is_primary} "
            + f"vertex='{x.vertex.model}' path.vertices_len={len(x.path.vertices)} "
            + f"path.edges_len={len(x.path.edges)} weights={x.path.weights}"
        )


def raw_in_manager(db: StandardDatabase):
    logger.info("\nraw_in_manager:")
    data: list[Operates] = (
        AQLManager(db)
        .add_for(For(Operates, alias="x"))
        .add_raw(Raw("SORT x.is_primary"))
        .list()
    )

    for x in data:
        logger.success(
            f"    last_maintenance='{x.last_maintenance}' is_primary={x.is_primary} "
            + f"operator='{x.vertex_from.nickname}' sensor='{x.vertex_to.model}'"
        )


def raw_return(db: StandardDatabase):
    logger.info("\nraw_return:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    ops: list = (
        AQLManager(db)
        .add_for(
            ForGraph(
                operator, "OUTBOUND", Operates, v_alias="v", e_alias="e", p_alias="p"
            )
        )
        .return_raw(Raw("p.weights"))
        .list()
    )

    for x in ops:
        logger.success(f"    weights={x}")


def raw_return_with_model(db: StandardDatabase):
    logger.info("\nraw_return_with_model:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    ops: list[Sensor] = (
        AQLManager(db)
        .add_for(
            ForGraph(
                operator, "OUTBOUND", Operates, v_alias="v", e_alias="e", p_alias="p"
            )
        )
        .return_raw(Raw("v"), return_model=Sensor)
        .list()
    )

    for x in ops:
        logger.success(f"    battery={x.battery_level} model={x.model}")


def raw_return_with_for_graph_edge(db: StandardDatabase):
    logger.info("\nraw_return_with_for_graph_edge:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    ops: list[Operates] = (
        AQLManager(db)
        .add_for(
            ff := ForGraph(
                operator, "OUTBOUND", Operates, v_alias="v", e_alias="e", p_alias="p"
            )
        )
        .return_raw(ff.return_edge(), return_model=Operates)
        .list()
    )

    for x in ops:
        logger.success(
            f"    last_maintenance='{x.last_maintenance}' is_primary={x.is_primary} "
            + f"operator='{x.vertex_from.nickname}' sensor='{x.vertex_to.model}'"
        )


def raw_return_with_for_graph_vertex(db: StandardDatabase):
    logger.info("\nraw_return_with_for_graph_vertex:")

    operator: Operator = AQLManager(db).get_by_id_or_key(Operator, "opp")

    ops: list[Operates] = (
        AQLManager(db)
        .add_for(
            ff := ForGraph(
                operator, "OUTBOUND", Operates, v_alias="v", e_alias="e", p_alias="p"
            )
        )
        .return_raw(ff.return_vertex(), return_model=Sensor)
        .list()
    )

    for x in ops:
        logger.success(f"     sensor='{x.model}'")


def raw_group_by(db: StandardDatabase):
    logger.info("\nraw_group_by:")
    # Usamos COLLECT dentro de un add_raw para agrupar
    data: list = (
        AQLManager(db)
        .add_for(For(Sensor, alias="s"))
        .add_raw(Raw("COLLECT status = s.status WITH COUNT INTO total"))
        .return_raw(Raw("{status: status, count: total}"))
        .list()
    )

    for x in data:
        logger.success(f"    Status: {x['status']} | Total: {x['count']}")


if __name__ == "__main__":
    with setup() as db:
        raw(db)
        raw_in_let(db)
        raw_how_value_in_filter(db)
        raw_in_filter(db)
        raw_inside_for(db)
        raw_in_manager(db)
        raw_return(db)
        raw_return_with_model(db)
        raw_return_with_for_graph_edge(db)
        raw_return_with_for_graph_vertex(db)
        raw_group_by(db)
