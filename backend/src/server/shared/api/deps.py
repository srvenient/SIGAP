import secrets
from typing import AsyncGenerator, Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from core.db import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]


async def require_device_key(x_device_key: Annotated[str | None, Header()] = None) -> None:
    """Autentica al worker de cámaras: las rutas que abren talanqueras no son públicas."""
    if not x_device_key or not secrets.compare_digest(x_device_key, settings.DEVICE_API_KEY):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Clave de dispositivo inválida")


DeviceKeyDep = Annotated[None, Depends(require_device_key)]
