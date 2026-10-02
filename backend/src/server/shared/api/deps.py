from typing import AsyncGenerator, Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from core.db import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]
