import asyncio
import sys
from typing import Any, AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.main import app
from src.server.shared.api.deps import get_db

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TEST_DATABASE_URL = "postgresql+psycopg://postgres:sigap@localhost:5433/sigap_test_db"


@pytest.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, Any]:
    async_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

    async with async_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: SQLModel.metadata.drop_all(sync_conn))
        await conn.run_sync(lambda sync_conn: SQLModel.metadata.create_all(sync_conn))

    yield async_engine

    await async_engine.dispose()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, Any]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        async with AsyncSession(
                bind=connection,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint"
        ) as session:
            yield session

        await transaction.rollback()


@pytest.fixture
async def async_client(db_session: AsyncSession):
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost:8000/api/v1") as client:
        yield client

    app.dependency_overrides.clear()
