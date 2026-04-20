from arango.database import StandardDatabase

from app.collections import Device, Interconnection
from app.database.aqlmanager import AQLManager, For, Let
from app.database.manager import CollectionManager


def test_for_simple(db: StandardDatabase):
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
            For(Device).filter((Device.name == "name A") | (Device.type == "type A"))
        )
        .list()
    )

    assert len(data) == 4

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
        Device(name="name A", type="type A"),
        Device(name="name B", type="type B"),
        Device(name="name C", type="type A"),
        Device(name="name D", type="type B"),
        Device(name="name E", type="type A"),
        Device(name="name F", type="type B"),
        Device(name="name G", type="type A"),
        Device(name="name H", type="type A"),
    ]
    cm.insert_many(devices)

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            ff := For(Device).filter(
                (Device.name == "name A") | (Device.type == "type A")
            )
        )
        .add_sort(ff.field(Device.name), "desc")
        .add_sort(ff.field(Device.type), "asc")
        .list()
    )

    assert len(data) == 5
    assert data[0].name == "name H"
    assert data[1].name == "name G"
    assert data[2].name == "name E"
    assert data[3].name == "name C"
    assert data[4].name == "name A"


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
        .add_let(fl := Let("name_let", "@val_type_a", bind_vars={"val_type_a": "type A"}))
        .add_for(For(Device).filter((Device.type == fl)))
        .list()
    )

    assert len(data) == 2

    data: list[Device] = (
        AQLManager(db)
        .add_let(
            fl := Let(
                "name_let",
                For(Device).filter(Device.type == "type B").subquery(Device.id),
            )
        )
        .add_for(For(Device).filter(Device.id.is_in(fl)))
        .list()
    )

    assert len(data) == 6

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            For(Device)
            .add_let(
                fl := Let(
                    "name_let",
                    For(Device, alias="inner")
                    .filter(Device.type == "type B")
                    .subquery(Device.id),
                )
            )
            .filter(Device.id.is_in(fl))
        )
        .list()
    )

    assert len(data) == 6
