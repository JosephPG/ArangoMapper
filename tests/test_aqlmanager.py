from arango.database import StandardDatabase

from app.aql.aqlmanager import AQLManager
from app.aql.operator import For, ForGraph, Let, Raw
from app.aql.schemas import GraphResponse
from app.collections import Device, Interconnection, Location, Owner
from app.database.manager import CollectionManager

from tests.utils import ReturnRawModelExample


def test_for_simple(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type A"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type A"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A", is_main=False),
        Device(name="name H", type="type B"),
    ]
    cm.insert_many(devices)

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device)
            .filter((Device.name == "name A") | (Device.type == "type A"))
            .filter(Device.is_main.is_true())
        )
        .list()
    )

    assert len(data) == 3

    for device_db in data:
        device_expected = next((x for x in devices if x.id == device_db.id))

        assert device_db.key == device_expected.key
        assert device_db.name == device_expected.name
        assert device_db.type == device_expected.type
        assert device_db.weight == device_expected.weight


def test_for_limit(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type A"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type A"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A"),
        Device(name="name H", type="type B"),
    ]
    cm.insert_many(devices)

    data: list[Device] = AQLManager(db).add_for(For(Device)).limit(4).list()

    assert len(data) == 4

    data: list[Device] = (
        AQLManager(db)
        .add_for(ff := For(Device))
        .add_sort(ff.field(Device.name))
        .limit(4, 4)
        .list()
    )

    assert data[0].name == "name E"
    assert data[1].name == "name F"
    assert data[2].name == "name G"
    assert data[3].name == "name H"

    data: list[Device] = AQLManager(db).add_for(For(Device)).limit(2).list()

    assert len(data) == 2


def test_for_sort(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A", is_main=False),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type A", is_main=False, weight=1),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type A", is_main=False, weight=1),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A", is_main=False, weight=1),
        Device(name="name H", type="type A"),
    ]
    cm.insert_many(devices)

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

    assert len(data) == 3
    assert data[0].name == "name G"
    assert data[1].name == "name E"
    assert data[2].name == "name C"


def test_for_nested(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type B"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type B"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A"),
        Device(name="name H", type="type B"),
    ]
    cm.insert_many(devices)

    interconnections = [
        Interconnection(type="itype A", vertex_from=devices[0], vertex_to=devices[1]),
        Interconnection(type="itype A", vertex_from=devices[2], vertex_to=devices[3]),
        Interconnection(type="itype A", vertex_from=devices[4], vertex_to=devices[5]),
        Interconnection(type="itype A", vertex_from=devices[6], vertex_to=devices[7]),
    ]
    cm.insert_many(interconnections)

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
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A", weight=1),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type B"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type B"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A"),
        Device(name="name H", type="type B"),
    ]
    cm.insert_many(devices)

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

    assert len(data) == 7


def test_for_let_for_with_let(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A", weight=1),
        Device(name="name B", type="type B", weight=5),
        Device(name="name C", type="type B", weight=5),
        Device(name="name D", type="type B", weight=10),
        Device(name="name E", type="type B", weight=5),
        Device(name="name F", type="type B", weight=5),
        Device(name="name G", type="type A", weight=20),
        Device(name="name H", type="type B", weight=5),
    ]
    cm.insert_many(devices)

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

    assert len(data) == 6


def test_for_let_for_subquery_raw(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A", weight=1),
        Device(name="name B", type="type B", weight=5),
        Device(name="name C", type="type B", weight=5),
        Device(name="name D", type="type B", weight=10),
        Device(name="name E", type="type B", weight=5),
        Device(name="name F", type="type B", weight=5),
        Device(name="name G", type="type A", weight=20),
        Device(name="name H", type="type B", weight=5),
    ]
    cm.insert_many(devices)

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

    assert len(data) == 6


def test_for_graph(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type B"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type B"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A"),
        Device(name="name H", type="type B"),
    ]
    cm.insert_many(devices)

    interconnections = [
        Interconnection(type="itype A", vertex_from=devices[0], vertex_to=devices[1]),
        Interconnection(type="itype A", vertex_from=devices[1], vertex_to=devices[2]),
        Interconnection(type="itype A", vertex_from=devices[2], vertex_to=devices[3]),
        Interconnection(type="itype A", vertex_from=devices[3], vertex_to=devices[4]),
        Interconnection(type="itype A", vertex_from=devices[5], vertex_to=devices[6]),
        Interconnection(type="itype A", vertex_from=devices[6], vertex_to=devices[7]),
    ]
    cm.insert_many(interconnections)

    data: list[GraphResponse] = (
        AQLManager(db)
        .add_for(ForGraph(devices[0], "OUTBOUND", Interconnection, max_d=3))
        .list()
    )

    assert len(data) == 3

    for res in data:
        assert isinstance(res.vertex, Device)
        assert isinstance(res.edge, Interconnection)

        for vertex in res.path.vertices:
            assert isinstance(vertex, Device)

        for edge in res.path.edges:
            assert isinstance(edge, Interconnection)

        for weight in res.path.weights:
            assert isinstance(weight, int)


def test_for_graph_filter(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type B"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type B"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A"),
        Device(name="name H", type="type B"),
    ]
    cm.insert_many(devices)

    interconnections = [
        Interconnection(type="itype A", vertex_from=devices[0], vertex_to=devices[1]),
        Interconnection(type="itype A", vertex_from=devices[1], vertex_to=devices[2]),
        Interconnection(type="itype A", vertex_from=devices[2], vertex_to=devices[3]),
        Interconnection(type="itype A", vertex_from=devices[3], vertex_to=devices[4]),
        Interconnection(type="itype A", vertex_from=devices[5], vertex_to=devices[6]),
        Interconnection(type="itype A", vertex_from=devices[6], vertex_to=devices[7]),
    ]
    cm.insert_many(interconnections)

    data: list[GraphResponse] = (
        AQLManager(db)
        .add_for(
            ForGraph(devices[0], "OUTBOUND", Interconnection, max_d=3)
            .filter(Device.name == "name B")
            .filter(Interconnection.type == "itype A")
        )
        .list()
    )

    assert len(data) == 1

    for res in data:
        assert isinstance(res.vertex, Device)
        assert isinstance(res.edge, Interconnection)

        for vertex in res.path.vertices:
            assert isinstance(vertex, Device)

        for edge in res.path.edges:
            assert isinstance(edge, Interconnection)

        for weight in res.path.weights:
            assert isinstance(weight, int)


def test_for_graph_different_vertex_start(db: StandardDatabase):
    cm = CollectionManager(db)

    locations: list[Location] = [
        Location(name="Location A"),
        Location(name="Location B"),
        Location(name="Location C"),
    ]

    cm.insert_many(locations)

    location_a, *_ = locations

    devices: list[Device] = [
        Device(name="device A", type="type A", weight=2),
        Device(name="device B", type="type B", weight=2),
        Device(name="device C", type="type A", weight=5),
        Device(name="device D", type="type B", weight=1),
        Device(name="device E", type="type A", weight=3),
        Device(name="device F", type="type A", weight=4),
    ]

    cm.insert_many(devices)

    device_a, *_ = devices

    cm.insert_many(
        [
            Owner(year=1, vertex_from=locations[0], vertex_to=devices[0]),
            Owner(year=2, vertex_from=locations[0], vertex_to=devices[1]),
            Owner(year=3, vertex_from=locations[0], vertex_to=devices[2]),
            Owner(year=1, vertex_from=locations[1], vertex_to=devices[3]),
            Owner(year=2, vertex_from=locations[1], vertex_to=devices[4]),
            Owner(year=3, vertex_from=locations[2], vertex_to=devices[5]),
        ]
    )

    data: list[GraphResponse] = (
        AQLManager(db).add_for(ForGraph(device_a, "INBOUND", Owner)).list()
    )

    for element in data:
        assert isinstance(element.vertex, Location)

    data: list[GraphResponse] = (
        AQLManager(db).add_for(ForGraph(location_a, "ANY", Owner)).list()
    )

    for element in data:
        assert isinstance(element.vertex, Device)


def test_for_let_for_graph_subquery(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type B"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type B"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A"),
        Device(name="name H", type="type B"),
    ]
    cm.insert_many(devices)

    interconnections = [
        Interconnection(type="itype A", vertex_from=devices[0], vertex_to=devices[1]),
        Interconnection(type="itype A", vertex_from=devices[1], vertex_to=devices[2]),
        Interconnection(type="itype A", vertex_from=devices[2], vertex_to=devices[3]),
        Interconnection(type="itype A", vertex_from=devices[3], vertex_to=devices[4]),
        Interconnection(type="itype A", vertex_from=devices[5], vertex_to=devices[6]),
        Interconnection(type="itype A", vertex_from=devices[6], vertex_to=devices[7]),
    ]
    cm.insert_many(interconnections)

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device)
            .add_let(
                fl := Let(
                    "name_let",
                    ForGraph(devices[0], "OUTBOUND", Interconnection)
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
                    ForGraph(devices[0], "OUTBOUND", Interconnection)
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
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type B"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type B"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A"),
        Device(name="name H", type="type B"),
    ]
    cm.insert_many(devices)

    data: list[Device] = (
        AQLManager(db)
        .add_let(
            fl := Let("name_let", Raw("@val_type_a", bind_vars={"val_type_a": "type A"}))
        )
        .add_for(For(Device).filter((Device.type == fl)))
        .list()
    )

    assert len(data) == 2


def test_raw_for_simple(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type A"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type A"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A"),
        Device(name="name H", type="type B"),
    ]
    cm.insert_many(devices)

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device)
            .add_raw(
                Raw(
                    "LET prefix = CONCAT(@pre, '', @sub)",
                    bind_vars={"pre": "name", "sub": "A"},
                ),
            )
            .filter((Device.name == Raw("prefix")) | (Device.type == "type A"))
        )
        .list()
    )

    assert len(data) == 4


def test_raw_filter(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type A"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type A"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A"),
        Device(name="name H", type="type B"),
    ]
    cm.insert_many(devices)

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device, alias="dvc").filter(
                Raw("dvc.name == @name", bind_vars={"name": "name A"})
                | (Device.type == "type A")
            )
        )
        .list()
    )

    assert len(data) == 4

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device, alias="dvc").filter(
                (Device.type == "type A")
                | Raw("dvc.name == @name", bind_vars={"name": "name A"})
            )
        )
        .list()
    )

    assert len(data) == 4


def test_return_raw(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type A"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type A"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A"),
        Device(name="name H", type="type B"),
    ]
    cm.insert_many(devices)

    data: list = (
        AQLManager(db)
        .add_for(
            For(Device, alias="dvc").filter(
                Raw("dvc.name == @name", bind_vars={"name": "name A"})
                | (Device.type == "type A")
            )
        )
        .return_raw(Raw("{other: dvc.name, cons: @valor}", bind_vars={"valor": 1}))
        .list()
    )

    assert len(data) == 4

    for element, name in zip(data, ["name A", "name C", "name E", "name G"]):
        assert element["other"] == name
        assert element["cons"] == 1


def test_return_raw_with_model(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type A"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type A"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A"),
        Device(name="name H", type="type B"),
    ]
    cm.insert_many(devices)

    data: list = (
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
        .list()
    )

    assert len(data) == 4

    for element, name in zip(data, ["name A", "name C", "name E", "name G"]):
        assert isinstance(element, ReturnRawModelExample)
        assert element.other == name
        assert element.cons == 1


def test_review(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
    ]
    cm.insert_many(devices)

    aql, bind_vars = (
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
        .review()
    )

    assert aql
    assert bind_vars


def test_first(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type A"),
        Device(name="name D", type="type B"),
    ]
    cm.insert_many(devices)

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
    assert device.name == "name C"


def test_last(db: StandardDatabase):
    cm = CollectionManager(db)

    devices = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type A"),
        Device(name="name D", type="type B"),
    ]
    cm.insert_many(devices)

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
    assert device.name == "name A"


def test_get_collection(db: StandardDatabase):
    cm = CollectionManager(db)

    devices: list[Device] = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
    ]
    cm.insert_many(devices)

    device: Device = AQLManager(db).get_by_id_or_key(Device, devices[0].id)

    assert isinstance(device, Device)
    assert device.name == "name A"


def test_get_edge(db: StandardDatabase):
    cm = CollectionManager(db)

    devices: list[Device] = [
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
    ]
    cm.insert_many(devices)

    edges: list[Interconnection] = [
        Interconnection(type="itype A", vertex_from=devices[0], vertex_to=devices[1]),
        Interconnection(type="itype B", vertex_from=devices[0], vertex_to=devices[1]),
    ]
    cm.insert_many(edges)

    inter: Interconnection = AQLManager(db).get_by_id_or_key(Interconnection, edges[0].id)

    assert isinstance(inter, Interconnection)
    assert inter.type == "itype A"
    assert inter.vertex_from.name == "name A"
    assert inter.vertex_to.name == "name B"


def test_count(db: StandardDatabase):
    cm = CollectionManager(db)

    cm.insert_many(
        [
            Device(name="name A", type="type A"),
            Device(name="name B", type="type B"),
            Device(name="name C", type="type B"),
            Device(name="name D", type="type B"),
        ]
    )

    count: int = AQLManager(db).add_for(For(Device)).count()

    assert count == 4


def test_nested(db: StandardDatabase):
    cm = CollectionManager(db)

    locations: list[Location] = [
        Location(name="Location A"),
        Location(name="Location B"),
        Location(name="Location C"),
    ]

    cm.insert_many(locations)

    location_a, *_ = locations

    devices: list[Device] = [
        Device(name="device A", type="type A", weight=2),
        Device(name="device B", type="type B", weight=2),
        Device(name="device C", type="type A", weight=5),
        Device(name="device D", type="type B", weight=1),
        Device(name="device E", type="type A", weight=3),
        Device(name="device F", type="type A", weight=4),
    ]

    cm.insert_many(devices)

    cm.insert_many(
        [
            Owner(year=1, vertex_from=locations[0], vertex_to=devices[0]),
            Owner(year=2, vertex_from=locations[0], vertex_to=devices[1]),
            Owner(year=3, vertex_from=locations[0], vertex_to=devices[2]),
            Owner(year=1, vertex_from=locations[1], vertex_to=devices[3]),
            Owner(year=2, vertex_from=locations[1], vertex_to=devices[4]),
            Owner(year=3, vertex_from=locations[2], vertex_to=devices[5]),
        ]
    )

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
    cm = CollectionManager(db)

    locations: list[Location] = [
        Location(name="Location A"),
        Location(name="Location B"),
        Location(name="Location C"),
    ]

    cm.insert_many(locations)

    location_a, *_ = locations

    devices: list[Device] = [
        Device(name="device A", type="type A", weight=2),
        Device(name="device B", type="type B", weight=2),
        Device(name="device C", type="type A", weight=5),
        Device(name="device D", type="type B", weight=1),
        Device(name="device E", type="type A", weight=3),
        Device(name="device F", type="type A", weight=4),
    ]

    cm.insert_many(devices)

    cm.insert_many(
        [
            Owner(year=1, vertex_from=locations[0], vertex_to=devices[0]),
            Owner(year=2, vertex_from=locations[0], vertex_to=devices[1]),
            Owner(year=3, vertex_from=locations[0], vertex_to=devices[2]),
            Owner(year=1, vertex_from=locations[1], vertex_to=devices[3]),
            Owner(year=2, vertex_from=locations[1], vertex_to=devices[4]),
            Owner(year=3, vertex_from=locations[2], vertex_to=devices[5]),
        ]
    )

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
