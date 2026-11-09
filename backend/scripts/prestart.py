"""Prepara la base de datos una sola vez, antes de levantar los workers de FastAPI."""
import asyncio
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from loguru import logger  # noqa: E402
from sqlalchemy import create_engine, inspect  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402

from core.config import settings  # noqa: E402
from core.db import AsyncSessionLocal, async_engine  # noqa: E402
from src.server.seed import seed  # noqa: E402

BASELINE_REVISION = "0001"
MAX_DB_WAIT_SECONDS = 60


def _wait_for_database(engine) -> None:
    deadline = time.monotonic() + MAX_DB_WAIT_SECONDS
    while True:
        try:
            with engine.connect():
                return
        except OperationalError:
            if time.monotonic() > deadline:
                raise
            logger.info("Esperando a PostgreSQL...")
            time.sleep(2)


def migrate() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))

    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    try:
        _wait_for_database(engine)
        tables = inspect(engine).get_table_names()
    finally:
        engine.dispose()

    # Base creada antes de Alembic: ya tiene el esquema inicial, así que no hay que recrearla
    if "users" in tables and "alembic_version" not in tables:
        logger.info("Base existente sin versión: se marca en {}", BASELINE_REVISION)
        command.stamp(config, BASELINE_REVISION)

    command.upgrade(config, "head")


async def run_seed() -> None:
    async with AsyncSessionLocal() as session:
        await seed(session)
    await async_engine.dispose()


if __name__ == "__main__":
    migrate()
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_seed())
    logger.success("Base de datos lista")
