from fastapi import FastAPI
from fastapi.routing import APIRoute
from loguru import logger
from sqlalchemy import text

from core.config import settings
from core.db import async_engine
from src.server.lifespan import lifespan


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Está es la API que expone los endpoints del proyecto",
    version=settings.PROJECT_VERSION,
    debug=settings.DEBUG,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan
)


@app.get("/health-check", tags=["Health"])
async def health_check():
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.exception("Health check failed: %s", e)
        return {"status": "error", "database": "disconnected"}
