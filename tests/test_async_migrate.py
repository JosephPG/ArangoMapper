import pytest
from arangoasync.database import StandardDatabase

from app.collections import Device, Interconnection, Location, Route
from app.database.async_migrate import async_migration

from tests.utils import async_delete_all_in_db


@pytest.mark.asyncio(loop_scope="session")
async def test_async_sync_migrate(async_db: StandardDatabase):
    await async_delete_all_in_db(async_db)

    await async_migration(async_db)

    assert await async_db.has_graph(Route._graph_name)
    assert await async_db.has_graph(Interconnection._graph_name)
    assert await async_db.has_collection(Location._collection_name)
    assert await async_db.has_collection(Device._collection_name)
    assert await async_db.has_collection(Route._collection_name)
    assert await async_db.has_collection(Interconnection._collection_name)
