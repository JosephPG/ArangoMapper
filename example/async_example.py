import asyncio

from arangoasync.database import StandardDatabase
from loguru import logger

from app.aql.async_aqlmanager import AsyncAQLManager
from app.aql.operator import For
from app.database.async_conn import AsyncConn
from app.database.async_manager import AsyncCollectionManager
from example.models import Operator, Sensor, Warehouse
from example.setup import setup


async def async_showcase(db: StandardDatabase):
    cm = AsyncCollectionManager(db)

    logger.info("Fase 1: Escritura")

    wh = Warehouse(name="Async Hub", capacity=500)

    await cm.insert(wh)

    logger.info("Fase 2: Lectura con AQL")

    await (
        AsyncAQLManager(db)
        .add_for(For(Sensor).filter(Sensor.status == "active"))
        .limit(5)
        .list()
    )

    logger.info("Fase 3: Ejecución en paralelo")

    tasks = [
        AsyncAQLManager(db).add_for(For(Warehouse)).count(),
        AsyncAQLManager(db).add_for(For(Sensor)).count(),
        AsyncAQLManager(db).add_for(For(Operator)).count(),
    ]

    counts = await asyncio.gather(
        *tasks
    )  # https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently
    logger.success(f"Totales en paralelo: {counts}")


async def run():
    db = await AsyncConn.async_get_db()
    await async_showcase(db)


if __name__ == "__main__":
    with setup() as _:
        asyncio.run(
            run()
        )  # https://docs.python.org/3/library/asyncio-runner.html#asyncio.run
