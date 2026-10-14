import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from loguru import logger

from core.db import init_db, async_engine, AsyncSessionLocal

from src.server.auth.infrastructure.postgres_refresh_token_repository import PostgresRefreshTokenRepository

CLEANUP_INTERVAL_SECONDS = 6 * 3600


async def _cleanup_refresh_tokens_loop() -> None:
    """Borra periódicamente los refresh tokens ya expirados."""
    while True:
        try:
            async with AsyncSessionLocal() as session:
                deleted = await PostgresRefreshTokenRepository(session).delete_expired()
            logger.info("Refresh tokens expirados eliminados: %s", deleted)
        except Exception:
            logger.exception("Falló la limpieza de refresh tokens")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("[STARTUP] Conectando a la base de datos...")
    try:
        await init_db()
        logger.info("[STARTUP] Base de datos inicializada correctamente")
    except Exception:
        logger.exception("[STARTUP] Error al inicializar la base de datos")
        raise

    logger.info("[STARTUP] Iniciando limpieza periódica de refresh tokens...")
    cleanup_task = asyncio.create_task(_cleanup_refresh_tokens_loop())
    logger.info("[STARTUP] Limpieza periódica de refresh tokens iniciada")

    logger.info("[STARTUP] Aplicación lista para recibir solicitudes")

    yield  # This is where the application runs

    # --- Shutdown ---
    logger.info("[SHUTDOWN] Cerrando la conexión a la base de datos...")
    await async_engine.dispose()
    logger.info("[SHUTDOWN] Conexión a la base de datos cerrada correctamente")

    logger.info("[SHUTDOWN] Cancelando limpieza periódica de refresh tokens...")
    cleanup_task.cancel()
    with suppress(asyncio.CancelledError):
        await cleanup_task
    logger.info("[SHUTDOWN] Limpieza periódica de refresh tokens cancelada")
