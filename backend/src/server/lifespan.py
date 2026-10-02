from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from core.db import init_db, async_engine

import src.server.models  # noqa: F401


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

    logger.info("[STARTUP] Aplicación lista para recibir solicitudes")

    yield  # This is where the application runs

    # --- Shutdown ---
    logger.info("[SHUTDOWN] Cerrando la conexión a la base de datos...")
    await async_engine.dispose()
    logger.info("[SHUTDOWN] Conexión a la base de datos cerrada correctamente")
