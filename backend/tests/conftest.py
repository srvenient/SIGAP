import asyncio
import os
import sys
from typing import Any, AsyncGenerator

# Antes de importar la app: las pruebas nunca deben conectarse a la base de desarrollo
os.environ.update({
    "POSTGRES_SERVER": "localhost",
    "POSTGRES_PORT": "5433",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "sigap",
    "POSTGRES_DB": "sigap_test_db",
    "ENVIRONMENT": "local",
    "DEVICE_TYPE": "cpu",
    "DEBUG": "false",
    "LOG_LEVEL": "info",
    "PROJECT_NAME": "sigap",
    "PROJECT_VERSION": "test",
    "SECRET_KEY": "test-secret-key-with-enough-length-0123456789",
    "FRONTEND_URL": "http://localhost:3000",
    "FIRST_SUPERUSER": "root",
    "FIRST_SUPERUSER_PASSWORD": "admin123",
    "DEVICE_API_KEY": "test-device-key-0123456789",
    "RATE_LIMIT_ENABLED": "false",
})

import pytest  # noqa: E402
from httpx import AsyncClient, ASGITransport  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402
from sqlmodel import SQLModel, select  # noqa: E402
from sqlmodel.ext.asyncio.session import AsyncSession  # noqa: E402

from core import immutable, security  # noqa: E402
from src.server import models  # noqa: E402, F401
from src.server.auth.domain.role.role import Role  # noqa: E402
from src.server.auth.domain.user.user import User  # noqa: E402
from src.server.main import app  # noqa: E402
from src.server.seed import seed  # noqa: E402
from src.server.shared.api.deps import get_db  # noqa: E402

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TEST_DATABASE_URL = "postgresql+psycopg://postgres:sigap@localhost:5433/sigap_test_db"
BASE_URL = "http://localhost:8000/api/v1"
DEVICE_HEADERS = {"X-Device-Key": "test-device-key-0123456789"}
PASSWORD = "Test12345"


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, Any]:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(text(immutable.CREATE_FUNCTION))
        for table in immutable.IMMUTABLE_TABLES:
            for statement in immutable.create_trigger_statements(table):
                await conn.execute(text(statement))

    async with AsyncSession(engine, expire_on_commit=False) as session:
        await seed(session)
        roles = {r.name: r for r in (await session.exec(select(Role))).all()}
        for username, role in (("admin1", "admin"), ("oper1", "operator"), ("oper2", "operator"), ("sup1", "support")):
            session.add(User(
                username=username,
                hashed_password=security.get_password_hash(PASSWORD),
                role_id=roles[role].id,
            ))
        await session.commit()

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, Any]:
    """Cada prueba corre en una transacción que se revierte al terminar."""
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        async with AsyncSession(
                bind=connection,
                expire_on_commit=False,
                autoflush=False,
                join_transaction_mode="create_savepoint"
        ) as session:
            yield session

        await transaction.rollback()


@pytest.fixture
async def async_client(db_session: AsyncSession):
    async def override_get_db():
        # Como en producción: lo que la petición no confirmó se descarta al terminar
        try:
            yield db_session
        finally:
            await db_session.rollback()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def login(async_client: AsyncClient):
    """Devuelve un cliente autenticado con el usuario indicado."""
    clients: list[AsyncClient] = []

    async def _login(username: str, password: str = PASSWORD) -> AsyncClient:
        client = AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL)
        response = await client.post("/auth/login", data={"username": username, "password": password})
        assert response.status_code == 200, response.text
        clients.append(client)
        return client

    yield _login

    for client in clients:
        await client.aclose()
