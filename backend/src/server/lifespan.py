import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from loguru import logger

from core.db import async_engine, AsyncSessionLocal

from src.server.auth.infrastructure.postgres_refresh_token_repository import PostgresRefreshTokenRepository
from src.server.wiring import build_device_service, build_payment_service

CLEANUP_INTERVAL_SECONDS = 6 * 3600
SWEEP_INTERVAL_SECONDS = 15


async def _cleanup_refresh_tokens_loop() -> None:
    """Borra periódicamente los refresh tokens ya expirados."""
    while True:
        try:
            async with AsyncSessionLocal() as session:
                deleted = await PostgresRefreshTokenRepository(session).delete_expired()
            logger.info("Refresh tokens expirados eliminados: {}", deleted)
        except Exception:
            logger.exception("Falló la limpieza de refresh tokens")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)


async def _operational_sweep_loop() -> None:
    """Detecta lo que ocurre por ausencia: worker sin reportar y pagos sin respuesta.

    Corre en cada worker de FastAPI; las consultas usan SKIP LOCKED y solo toman filas aún sin
    procesar, así que cada caso se atiende una sola vez.
    """
    while True:
        try:
            async with AsyncSessionLocal() as session:
                await build_device_service(session).sweep_stale()
            async with AsyncSessionLocal() as session:
                await build_payment_service(session).expire_overdue()
        except Exception:
            logger.exception("Falló el barrido operativo")
        await asyncio.sleep(SWEEP_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [
        asyncio.create_task(_cleanup_refresh_tokens_loop()),
        asyncio.create_task(_operational_sweep_loop()),
    ]
    logger.info("[STARTUP] Aplicación lista para recibir solicitudes")

    yield  # This is where the application runs

    for task in tasks:
        task.cancel()
    for task in tasks:
        with suppress(asyncio.CancelledError):
            await task

    await async_engine.dispose()
    logger.info("[SHUTDOWN] Conexión a la base de datos cerrada correctamente")
