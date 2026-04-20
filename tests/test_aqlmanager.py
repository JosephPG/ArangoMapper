from arango.database import StandardDatabase

from app.collections import Device, Interconnection
from app.database.aqlmanager import AQLManager, For
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

    data: list[Device] = (
        AQLManager(db)
        .add_for(
            first_for := For(Device, alias="doc_from").filter(
                (Device.name == "name A") | (Device.type == "type A")
            )
        )
        .add_for(
            For(Interconnection).filter(
                (Interconnection.id_from == first_for.field(Device.id))
            )
        )
        .list()
    )

    assert len(data) == 2

    for interc_db in data:
        interc_expected = next((x for x in interconnections if x.id == interc_db.id))

        assert interc_db.key == interc_expected.key
        assert interc_db.vertex_from.model_dump(
            by_alias=True
        ) == interc_expected.vertex_from.model_dump(by_alias=True)
        assert interc_db.vertex_to.model_dump(
            by_alias=True
        ) == interc_expected.vertex_to.model_dump(by_alias=True)
