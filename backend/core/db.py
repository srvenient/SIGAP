from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings

async_engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=settings.DEBUG, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """
    Initialize the database with initial data.
    This function should contain the logic to create tables and insert initial data.
    """
    # Create all the tables
    async with async_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: SQLModel.metadata.create_all(sync_conn))
