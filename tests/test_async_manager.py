import pytest
from arangoasync.database import StandardDatabase

from app.aql.aqlmanager import AsyncAQLManager
from app.aql.operator import For
from app.collections import Device, Interconnection, Location, Route
from app.database.async_manager import AsyncCollectionManager


@pytest.mark.asyncio(loop_scope="session")
async def test_async_manager_insert_not_id_and_key(async_db: StandardDatabase):
    cm = AsyncCollectionManager(async_db)

    location = Location(name="local A")
    await cm.insert(location)

    assert location.id
    assert location.key
    assert location.name == "local A"


@pytest.mark.asyncio(loop_scope="session")
async def test_async_manager_insert_with_id_and_key(async_db: StandardDatabase):
    cm = AsyncCollectionManager(async_db)

    location = Location(_id="locations/1234", _key="1234", name="local A")
    await cm.insert(location)

    assert location.id == "locations/1234"
    assert location.key == "1234"
    assert location.name == "local A"


@pytest.mark.asyncio(loop_scope="session")
async def test_async_manager_insert_graph(async_db: StandardDatabase):
    cm = AsyncCollectionManager(async_db)

    first_location = Location(name="local A")
    await cm.insert(first_location)

    second_location = Location(name="local B")
    await cm.insert(second_location)

    route = Route(vertex_from=first_location, vertex_to=second_location)
    await cm.insert_graph(route)

    assert route.id
    assert route.key
    assert route.vertex_from.id
    assert route.vertex_from.name == "local A"
    assert route.vertex_to.id
    assert route.vertex_to.name == "local B"


@pytest.mark.asyncio(loop_scope="session")
async def test_async_manager_update(async_db: StandardDatabase):
    cm = AsyncCollectionManager(async_db)

    location = Location(_key="1234", name="local A")
    await cm.insert(location)

    location.name = "local changed"
    await cm.update(location)

    assert location.id
    assert location.key == "1234"
    assert location.name == "local changed"


@pytest.mark.asyncio(loop_scope="session")
async def test_async_manager_update_graph(async_db: StandardDatabase):
    cm = AsyncCollectionManager(async_db)

    first_device = Device(name="device A", type="engine")
    await cm.insert(first_device)

    second_device = Device(name="device B", type="engine")
    await cm.insert(second_device)

    interconnection = Interconnection(
        _key="1234", vertex_from=first_device, vertex_to=second_device, type="wire"
    )
    await cm.insert_graph(interconnection)

    assert interconnection.type == "wire"

    interconnection.type = "antenna"

    await cm.update(interconnection)

    assert interconnection.id
    assert interconnection.key == "1234"
    assert interconnection.type == "antenna"


@pytest.mark.asyncio(loop_scope="session")
async def test_async_manager_insert_many(async_db: StandardDatabase):
    cm = AsyncCollectionManager(async_db)

    locations = [
        Location(name="local A"),
        Location(name="local B"),
        Location(name="local C"),
        Location(name="local D"),
        Location(name="local E"),
    ]

    await cm.insert_many(locations)

    expected_names = ["local A", "local B", "local C", "local D", "local E"]

    for location, name in zip(locations, expected_names):
        assert location.id
        assert location.key
        assert location.name == name


@pytest.mark.asyncio(loop_scope="session")
async def test_async_manager_insert_many_graph(async_db: StandardDatabase):
    cm = AsyncCollectionManager(async_db)

    locations = [
        Location(name="local A"),
        Location(name="local B"),
        Location(name="local C"),
        Location(name="local D"),
        Location(name="local E"),
        Location(name="local F"),
    ]
    await cm.insert_many(locations)

    routes = [
        Route(vertex_from=locations[0], vertex_to=locations[1]),
        Route(vertex_from=locations[2], vertex_to=locations[3]),
        Route(vertex_from=locations[4], vertex_to=locations[5]),
    ]
    await cm.insert_many(routes)

    for route in routes:
        assert route.id
        assert route.key
        assert route.id_from
        assert route.id_to


@pytest.mark.asyncio(loop_scope="session")
async def test_async_manager_delete(async_db: StandardDatabase):
    cm = AsyncCollectionManager(async_db)

    location = Location(_id="locations/1234", _key="1234", name="local A")
    await cm.insert(location)

    assert await AsyncAQLManager(async_db).get_by_id_or_key(Location, "1234")

    await cm.delete(location)

    assert not await AsyncAQLManager(async_db).get_by_id_or_key(Location, "1234")


@pytest.mark.asyncio(loop_scope="session")
async def test_async_manager_delete_edge(async_db: StandardDatabase):
    cm = AsyncCollectionManager(async_db)

    first_location = Location(name="local A")
    await cm.insert(first_location)

    second_location = Location(name="local B")
    await cm.insert(second_location)

    route = Route(vertex_from=first_location, vertex_to=second_location)
    await cm.insert_graph(route)

    assert await AsyncAQLManager(async_db).get_by_id_or_key(Route, route.id)

    await cm.delete(route)

    assert not await AsyncAQLManager(async_db).get_by_id_or_key(Route, route.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_async_manager_delete_many(async_db: StandardDatabase):
    cm = AsyncCollectionManager(async_db)

    locations = [
        Location(name="local A"),
        Location(name="local B"),
        Location(name="local C"),
        Location(name="local D"),
    ]
    await cm.insert_many(locations)

    assert await AsyncAQLManager(async_db).add_for(For(Location)).count() == 4

    await cm.delete_many(locations)

    assert not await AsyncAQLManager(async_db).add_for(For(Location)).count()


@pytest.mark.asyncio(loop_scope="session")
async def test_async_manager_delete_many_graphs(async_db: StandardDatabase):
    cm = AsyncCollectionManager(async_db)

    locations = [
        Location(name="local A"),
        Location(name="local B"),
        Location(name="local C"),
        Location(name="local D"),
        Location(name="local E"),
        Location(name="local F"),
    ]
    await cm.insert_many(locations)

    routes = [
        Route(vertex_from=locations[0], vertex_to=locations[1]),
        Route(vertex_from=locations[2], vertex_to=locations[3]),
        Route(vertex_from=locations[4], vertex_to=locations[5]),
    ]
    await cm.insert_many(routes)

    assert await AsyncAQLManager(async_db).add_for(For(Route)).count() == 3

    await cm.delete_many(routes)

    assert not await AsyncAQLManager(async_db).add_for(For(Route)).count()
