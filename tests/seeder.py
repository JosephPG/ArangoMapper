from arango.database import StandardDatabase
from arangoasync.database import StandardDatabase as AsyncStandardDatabase

from arangomapper.collections import Device, Interconnection, Location, Owner
from arangomapper.database.async_manager import AsyncCollectionManager
from arangomapper.database.manager import CollectionManager


def devices_seeder(db: StandardDatabase) -> list[Device]:
    cm = CollectionManager(db)

    devices: list[Device] = [
        Device(name="Dev 1", type="type A", is_main=False, weight=5),
        Device(name="Dev 2", type="type B", is_main=False, weight=15),
        Device(name="Dev 3", type="type A", is_main=False, weight=10),
        Device(name="Dev 4", type="type B", is_main=False, weight=4),
        Device(name="Dev 5", type="type A", is_main=False, weight=15),
        Device(name="Dev 6", type="type B", is_main=False, weight=8),
        # --- GRUPO 2: Fallan por Peso (Límites) ---
        Device(
            name="Dev 7", type="type A", is_main=False, weight=4
        ),  # Límite inferior (falla)
        Device(
            name="Dev 8", type="type B", is_main=False, weight=16
        ),  # Límite superior (falla)
        Device(name="Dev 9", type="type A", is_main=False, weight=3),  # Fuera de rango
        Device(name="Dev 10", type="type B", is_main=False, weight=20),  # Fuera de rango
        # --- GRUPO 3: Fallan por is_main (No declarado o True) ---
        Device(name="Dev 11", type="type A", weight=10),  # is_main no declarado
        Device(
            name="Dev 12", type="type B", is_main=True, weight=10
        ),  # is_main True explícito
        Device(name="Dev 13", type="type A", weight=7),  # is_main no declarado
        Device(
            name="Dev 14", type="type B", is_main=True, weight=12
        ),  # is_main True explícito
        # --- GRUPO 4: Éxitos adicionales para volumen ---
        Device(name="Dev 15", type="type A", is_main=False, weight=6),
        Device(name="Dev 16", type="type B", is_main=False, weight=14),
        Device(name="Dev 17", type="type A", is_main=False, weight=11),
        Device(name="Dev 18", type="type B", is_main=False, weight=9),
        # --- GRUPO 5: Casos borde y ruidos ---
        Device(name="Dev 19", type="type A", is_main=False, weight=4),  # Casi entra
        Device(name="Dev 20", type="type B", is_main=False, weight=15),  # Casi sale
        Device(name="Dev 21", type="type A", weight=15),  # Peso OK, pero is_main omitido
        Device(name="Dev 22", type="type B", is_main=False, weight=5),
    ]

    cm.insert_many(devices)

    return devices


def interconnections_seeder(
    db: StandardDatabase,
) -> tuple[list[Interconnection], list[Device]]:
    cm = CollectionManager(db)

    devices: list[Device] = [
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

    dev_a, dev_b, dev_c, dev_d, dev_e, dev_f, dev_g, dev_h = devices

    interconnections: list[Interconnection] = [
        Interconnection(type="itype A", vertex_from=dev_a, vertex_to=dev_b),
        Interconnection(type="itype A", vertex_from=dev_b, vertex_to=dev_c),
        Interconnection(type="itype A", vertex_from=dev_c, vertex_to=dev_d),
        Interconnection(type="itype A", vertex_from=dev_d, vertex_to=dev_e),
        Interconnection(type="itype A", vertex_from=dev_f, vertex_to=dev_g),
        Interconnection(type="itype A", vertex_from=dev_g, vertex_to=dev_h),
    ]
    cm.insert_many(interconnections)

    return interconnections, devices


def owners_seeder(
    db: StandardDatabase,
) -> tuple[list[Owner], list[Location], list[Device]]:
    cm = CollectionManager(db)

    locations: list[Location] = [
        Location(name="Location A"),
        Location(name="Location B"),
        Location(name="Location C"),
    ]
    cm.insert_many(locations)

    devices: list[Device] = [
        Device(name="device A", type="type A", weight=2),
        Device(name="device B", type="type B", weight=2),
        Device(name="device C", type="type A", weight=5),
        Device(name="device D", type="type B", weight=1),
        Device(name="device E", type="type A", weight=3),
        Device(name="device F", type="type A", weight=4),
    ]
    cm.insert_many(devices)

    local_a, local_b, local_c = locations
    dev_a, dev_b, dev_c, dev_d, dev_e, dev_f = devices

    owners: list[Owner] = [
        Owner(year=1, vertex_from=local_a, vertex_to=dev_a),
        Owner(year=2, vertex_from=local_a, vertex_to=dev_b),
        Owner(year=3, vertex_from=local_a, vertex_to=dev_c),
        Owner(year=1, vertex_from=local_b, vertex_to=dev_d),
        Owner(year=2, vertex_from=local_b, vertex_to=dev_e),
        Owner(year=3, vertex_from=local_c, vertex_to=dev_f),
    ]
    cm.insert_many(owners)

    return owners, locations, devices


async def async_device_seeder(async_db: AsyncStandardDatabase) -> list[Device]:
    cm = AsyncCollectionManager(async_db)

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

    await cm.insert_many(devices)

    return devices
