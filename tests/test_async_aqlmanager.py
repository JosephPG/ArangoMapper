import pytest
from arangoasync.database import StandardDatabase

from app.aql.async_aqlmanager import AsyncAQLManager
from app.aql.operator import For, Raw
from app.collections import Device

from tests.seeder import async_device_seeder


@pytest.mark.asyncio(loop_scope="session")
async def test_async_for_simple(async_db: StandardDatabase):
    devices: list[Device] = await async_device_seeder(async_db)

    data: list[Device] = await (
        AsyncAQLManager(async_db)
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


@pytest.mark.asyncio(loop_scope="session")
async def test_async_count(async_db: StandardDatabase):
    await async_device_seeder(async_db)

    count: int = await AsyncAQLManager(async_db).add_for(For(Device)).count()

    assert count == 8


@pytest.mark.asyncio(loop_scope="session")
async def test_async_get_collection(async_db: StandardDatabase):
    device, *_ = await async_device_seeder(async_db)

    device: Device = await AsyncAQLManager(async_db).get_by_id_or_key(Device, device.id)

    assert isinstance(device, Device)
    assert device.name == "name A"


@pytest.mark.asyncio(loop_scope="session")
async def test_first(async_db: StandardDatabase):
    await async_device_seeder(async_db)

    device: Device = await (
        AsyncAQLManager(async_db)
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
    assert device.name == "name G"


@pytest.mark.asyncio(loop_scope="session")
async def test_last(async_db: StandardDatabase):
    await async_device_seeder(async_db)

    device: Device = await (
        AsyncAQLManager(async_db)
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
