from arango.database import StandardDatabase

from arangomapper.aql.aqlmanager import AQLManager
from arangomapper.aql.operator import For, ForGraph, Let, Raw
from arangomapper.aql.schemas import GraphResponse
from arangomapper.collections import Device, Interconnection, Location, Owner

from tests.seeder import devices_seeder, interconnections_seeder, owners_seeder
from tests.utils import ReturnRawModelExample


def test_for_simple(db: StandardDatabase):
    devices = devices_seeder(db)

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device)
            .filter((Device.name == "name A") | (Device.type == "type A"))
            .filter((Device.is_main.is_false()) & (Device.weight.is_not_null()))
        )
        .list()
    )

    assert len(data) == 8

    for device_db in data:
        device_expected = next((x for x in devices if x.id == device_db.id))

        assert device_db.key == device_expected.key
        assert device_db.name == device_expected.name
        assert device_db.type == device_expected.type
        assert device_db.weight == device_expected.weight


def test_for_sort(db: StandardDatabase):
    devices_seeder(db)

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            ff := For(Device)
            .filter((Device.name == "name A") | (Device.type == "type A"))
            .filter((Device.is_main.is_false()) & (Device.weight.is_not_null()))
        )
        .add_sort(ff.field(Device.name), "desc")
        .add_sort(ff.field(Device.type), "asc")
        .list()
    )

    assert len(data) == 8
    assert data[0].name == "Dev 9"
    assert data[1].name == "Dev 7"
    assert data[2].name == "Dev 5"


def test_for_limit(db: StandardDatabase):
    devices_seeder(db)

    data: list[Device] = AQLManager(db).add_for(For(Device)).limit(4).list()

    assert len(data) == 4

    data: list[Device] = (
        AQLManager(db)
        .add_for(ff := For(Device))
        .add_sort(ff.field(Device.name))
        .limit(4, 4)
        .list()
    )

    assert data[0].name == "Dev 13"
    assert data[1].name == "Dev 14"
    assert data[2].name == "Dev 15"
    assert data[3].name == "Dev 16"

    data: list[Device] = AQLManager(db).add_for(For(Device)).limit(2).list()

    assert len(data) == 2


def test_for_nested(db: StandardDatabase):
    interconnections, _ = interconnections_seeder(db)

    data: list[Interconnection] = (
        AQLManager(db)
        .add_for(
            ff := For(Device, alias="doc_from").filter(
                (Device.name == "name A") | (Device.type == "type A")
            )
        )
        .add_for(
            For(Interconnection).filter((Interconnection.id_from == ff.field(Device.id)))
        )
        .add_sort(ff.field(Device.name), "desc")
        .list()
    )

    assert len(data) == 2
    assert data[0].vertex_from.name == "name G"

    for interc_db in data:
        interc_expected = next((x for x in interconnections if x.id == interc_db.id))

        assert interc_db.key == interc_expected.key
        assert interc_db.vertex_from.model_dump(
            by_alias=True
        ) == interc_expected.vertex_from.model_dump(by_alias=True)
        assert interc_db.vertex_to.model_dump(
            by_alias=True
        ) == interc_expected.vertex_to.model_dump(by_alias=True)


def test_for_let(db: StandardDatabase):
    devices_seeder(db)

    data: list[Device] = (
        AQLManager(db)
        .add_let(
            fl := Let(
                "name_let",
                For(Device)
                .filter((Device.type == "type B") | (Device.weight.is_null()))
                .subquery(Device.id),
            )
        )
        .add_for(For(Device).filter(Device.id.is_in(fl)))
        .list()
    )

    assert len(data) == 11


def test_for_let_for_with_let(db: StandardDatabase):
    devices_seeder(db)

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device)
            .add_let(
                fl := Let(
                    "name_let",
                    For(Device, alias="inner")
                    .filter((Device.weight >= 5) & (Device.weight <= 15))
                    .subquery(Device.id),
                )
            )
            .filter(Device.id.is_in(fl))
        )
        .list()
    )

    assert len(data) == 16


def test_for_let_for_subquery_raw(db: StandardDatabase):
    devices_seeder(db)

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device)
            .add_let(
                fl := Let(
                    "name_let",
                    For(Device, alias="inner")
                    .filter((Device.weight > 4) & (Device.weight < 15))
                    .subquery_raw(Raw("inner.name")),
                )
            )
            .filter(Device.name.is_in(fl))
        )
        .list()
    )

    assert len(data) == 12


def test_for_graph(db: StandardDatabase):
    _, devices = interconnections_seeder(db)
    device_a: Device = devices[0]

    data: list[GraphResponse] = (
        AQLManager(db)
        .add_for(ForGraph(device_a, "OUTBOUND", Interconnection, max_d=3))
        .list()
    )

    assert len(data) == 3

    for res in data:
        assert isinstance(res.vertex, Device)
        assert isinstance(res.edge, Interconnection)

        assert all(isinstance(vertex, Device) for vertex in res.path.vertices)
        assert all(isinstance(edge, Interconnection) for edge in res.path.edges)

        for weight in res.path.weights:
            assert isinstance(weight, int)


def test_for_graph_filter(db: StandardDatabase):
    _, devices = interconnections_seeder(db)
    device_a: Device = devices[0]

    data: list[GraphResponse] = (
        AQLManager(db)
        .add_for(
            ForGraph(device_a, "OUTBOUND", Interconnection, max_d=3)
            .filter(Device.name == "name B")
            .filter(Interconnection.type == "itype A")
        )
        .list()
    )

    assert len(data) == 1

    res = data[0]

    assert isinstance(res.vertex, Device)
    assert isinstance(res.edge, Interconnection)

    assert all(isinstance(vertex, Device) for vertex in res.path.vertices)

    assert all(isinstance(edge, Interconnection) for edge in res.path.edges)

    for weight in res.path.weights:
        assert isinstance(weight, int)


def test_for_graph_different_vertex_start(db: StandardDatabase):
    _, locations, devices = owners_seeder(db)

    location_a: Location = locations[0]
    device_a: Device = devices[0]

    data: list[GraphResponse] = (
        AQLManager(db).add_for(ForGraph(device_a, "INBOUND", Owner)).list()
    )

    assert len(data) > 0
    assert all(isinstance(element.vertex, Location) for element in data)

    data: list[GraphResponse] = (
        AQLManager(db).add_for(ForGraph(location_a, "ANY", Owner)).list()
    )

    assert len(data) > 0
    assert all(isinstance(element.vertex, Device) for element in data)


def test_for_let_for_graph_subquery(db: StandardDatabase):
    _, devices = interconnections_seeder(db)
    device_a: Device = devices[0]

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device)
            .add_let(
                fl := Let(
                    "name_let",
                    ForGraph(device_a, "OUTBOUND", Interconnection)
                    .filter(Device.type == "type B")
                    .subquery(Device.name),
                )
            )
            .filter(Device.name.is_in(fl))
        )
        .list()
    )

    assert len(data) == 1

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device)
            .add_let(
                fl := Let(
                    "name_let",
                    ForGraph(device_a, "OUTBOUND", Interconnection)
                    .filter(Device.type == "type B")
                    .subquery(Interconnection.id_to),
                )
            )
            .filter(Device.id.is_in(fl))
        )
        .list()
    )

    assert len(data) == 1


def test_for_raw_let(db: StandardDatabase):
    devices_seeder(db)

    data: list[Device] = (
        AQLManager(db)
        .add_let(
            fl := Let("name_let", Raw("@val_type_a", bind_vars={"val_type_a": "type A"}))
        )
        .add_for(For(Device).filter((Device.type == fl)))
        .list()
    )

    assert len(data) == 11


def test_raw_for_simple(db: StandardDatabase):
    devices_seeder(db)

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device)
            .add_raw(
                Raw(
                    "LET prefix = CONCAT(@pre, '', @sub)",
                    bind_vars={"pre": "Dev ", "sub": "14"},
                ),
            )
            .filter((Device.name == Raw("prefix")) | (Device.type == "type A"))
        )
        .list()
    )

    assert len(data) == 12


def test_raw_filter(db: StandardDatabase):
    devices_seeder(db)

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device, alias="dvc").filter(
                Raw("dvc.name == @name", bind_vars={"name": "Dev 18"})
                | (Device.type == "type A")
            )
        )
        .list()
    )

    assert len(data) == 12

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device, alias="dvc").filter(
                (Device.type == "type A")
                | Raw("dvc.name == @name", bind_vars={"name": "Dev 22"})
            )
        )
        .list()
    )

    assert len(data) == 12


def test_return_raw(db: StandardDatabase):
    devices_seeder(db)

    data: list = (
        AQLManager(db)
        .add_for(
            For(Device, alias="dvc").filter(
                Raw("dvc.name == @name", bind_vars={"name": "Dev 22"})
                | (Device.type == "type A")
            )
        )
        .return_raw(Raw("{other: dvc.name, cons: @valor}", bind_vars={"valor": 1}))
        .list()
    )

    assert len(data) == 12

    for element, name in zip(
        data,
        [
            "Dev 1",
            "Dev 3",
            "Dev 5",
            "Dev 7",
            "Dev 9",
            "Dev 11",
            "Dev 13",
            "Dev 15",
            "Dev 17",
            "Dev 19",
            "Dev 21",
            "Dev 22",
        ],
    ):
        assert element["other"] == name
        assert element["cons"] == 1


def test_return_raw_with_model(db: StandardDatabase):
    devices_seeder(db)

    data: list = (
        AQLManager(db)
        .add_for(
            For(Device, alias="dvc").filter(
                Raw("dvc.name == @name", bind_vars={"name": "Dev 22"})
                | (Device.type == "type A")
            )
        )
        .return_raw(
            Raw("{other: dvc.name, cons: @valor}", bind_vars={"valor": 1}),
            ReturnRawModelExample,
        )
        .list()
    )

    assert len(data) == 12

    for element, name in zip(
        data,
        [
            "Dev 1",
            "Dev 3",
            "Dev 5",
            "Dev 7",
            "Dev 9",
            "Dev 11",
            "Dev 13",
            "Dev 15",
            "Dev 17",
            "Dev 19",
            "Dev 21",
            "Dev 22",
        ],
    ):
        assert isinstance(element, ReturnRawModelExample)
        assert element.other == name
        assert element.cons == 1


def test_review(db: StandardDatabase):
    devices_seeder(db)

    manager: AQLManager = (
        AQLManager(db)
        .add_for(
            For(Device, alias="dvc").filter(
                Raw("dvc.name == @name", bind_vars={"name": "name A"})
                | (Device.type == "type A")
            )
        )
        .return_raw(
            Raw("{other: dvc.name, cons: @valor}", bind_vars={"valor": 1}),
            ReturnRawModelExample,
        )
    )

    assert manager.list()

    assert manager.aql_review
    assert manager.bind_vars_review


def test_first(db: StandardDatabase):
    devices_seeder(db)

    device: Device = (
        AQLManager(db)
        .add_for(
            ff := For(Device, alias="dvc").filter(
                Raw("dvc.name == @name", bind_vars={"name": "name A"})
                | (Device.type == "type A")
            )
        )
        .add_sort(ff.field(Device.name), "desc")
        .first()
    )

    assert isinstance(device, Device)
    assert device.name == "Dev 9"


def test_last(db: StandardDatabase):
    devices_seeder(db)

    device: Device = (
        AQLManager(db)
        .add_for(
            ff := For(Device, alias="dvc").filter(
                Raw("dvc.name == @name", bind_vars={"name": "name A"})
                | (Device.type == "type A")
            )
        )
        .add_sort(ff.field(Device.name), "desc")
        .last()
    )

    assert isinstance(device, Device)
    assert device.name == "Dev 1"


def test_get_collection(db: StandardDatabase):
    devices: list[Device] = devices_seeder(db)
    dev: Device = devices[0]

    device: Device = AQLManager(db).get_by_id_or_key(Device, dev.id)

    assert isinstance(device, Device)
    assert device.name == "Dev 1"


def test_get_edge(db: StandardDatabase):
    interconnections, _ = interconnections_seeder(db)
    interconnection: Interconnection = interconnections[0]

    inter: Interconnection = AQLManager(db).get_by_id_or_key(
        Interconnection, interconnection.id
    )

    assert isinstance(inter, Interconnection)
    assert inter.type == "itype A"
    assert inter.vertex_from.name == "name A"
    assert inter.vertex_to.name == "name B"


def test_count(db: StandardDatabase):
    devices_seeder(db)

    count: int = AQLManager(db).add_for(For(Device)).count()

    assert count == 22


def test_nested(db: StandardDatabase):
    _, locations, _ = owners_seeder(db)

    location_a: Location = locations[0]

    data: list[Device] = (
        AQLManager(db)
        .add_let(fl := Let("peso_minimo", Raw("@peso", bind_vars={"peso": 2})))
        .add_for(ffg := ForGraph(location_a, "OUTBOUND", Owner))
        .add_for(
            ff := For(Device)
            .filter((Device.type == "type A") & (Device.weight >= fl))
            .filter((Device.id) == ffg.field(Device.id))
        )
        .add_sort(ff.field(Device.name))
        .list()
    )

    assert len(data) == 2

    for device, name in zip(data, ["device A", "device C"]):
        assert device.name == name


def test_nested_return_raw(db: StandardDatabase):
    _, locations, _ = owners_seeder(db)

    location_a: Location = locations[0]

    owners: list[Owner] = (
        AQLManager(db)
        .add_let(fl := Let("peso_minimo", Raw("@peso", bind_vars={"peso": 2})))
        .add_for(ffg := ForGraph(location_a, "OUTBOUND", Owner, e_alias="edge"))
        .add_for(
            For(Device)
            .filter((Device.type == "type A") & (Device.weight >= fl))
            .filter((Device.id) == ffg.field(Device.id))
        )
        .add_sort(ffg.field(Owner.year), "desc")
        .return_raw(ffg.return_edge(), return_model=Owner)
        .list()
    )

    assert len(owners) == 2

    for owner, year in zip(owners, [3, 1]):
        assert owner.year == year
        assert owner.vertex_from
        assert owner.vertex_to


def test_bind_vars(db: StandardDatabase):
    _, locations, _ = owners_seeder(db)

    location_a: Location = locations[0]

    aql_manager: AQLManager = (
        AQLManager(db)
        .add_let(fl := Let("peso_minimo", Raw("@peso", bind_vars={"peso": 2})))
        .add_for(ffg := ForGraph(location_a, "OUTBOUND", Owner, e_alias="edge"))
        .add_for(
            For(Device)
            .filter((Device.type == "type A") & (Device.weight >= fl))
            .filter((Device.id) == ffg.field(Device.id))
        )
        .add_sort(ffg.field(Owner.year), "desc")
        .return_raw(ffg.return_edge(), return_model=Owner)
    )

    aql_manager.list()

    assert aql_manager.bind_vars_review["bindvar_1"] == 2
    assert aql_manager.bind_vars_review["bindvar_2"] == "type A"
