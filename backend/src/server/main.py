from fastapi import FastAPI
from fastapi.routing import APIRoute
from loguru import logger
from sqlalchemy import text
from starlette.responses import JSONResponse

from core.config import settings
from core.db import async_engine
from core.rate_limit import limiter
from src.server.lifespan import lifespan
from src.server.auth.api.exception_handlers import register_auth_errors
from src.server.auth.api.auth_router import auth_router
from src.server.auth.api.user_router import user_router


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

app.state.limiter = limiter

if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=settings.all_cors_origins,  # type: ignore
        allow_credentials=True,  # type: ignore
        allow_methods=["*"],  # type: ignore
        allow_headers=["*"],  # type: ignore
    )


@app.get("/health-check", tags=["Health"])
async def health_check():
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        logger.exception("Health check failed")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "disconnected"},
        )


register_auth_errors(app)

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(user_router, prefix=settings.API_V1_STR)
