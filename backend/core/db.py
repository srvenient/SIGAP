from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from src.server.auth.application.user_service import UserService
from src.server.auth.infrastructure.postgres_refresh_token_repository import PostgresRefreshTokenRepository
from src.server.auth.infrastructure.postgres_role_repository import PostgresRoleRepository
from src.server.auth.infrastructure.postgres_user_repository import PostgresUserRepository

async_engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=settings.DEBUG, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    from src.server.auth.domain.role.role import Role, RoleName, ROLE_DESCRIPTIONS
    from src.server.auth.domain.user.user import User, UserCreate
    from src.server.transaction.domain.transaction import Transaction

    async with async_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: SQLModel.metadata.create_all(sync_conn))

    async with AsyncSessionLocal() as session:
        for role_name in RoleName:
            existing = (await session.exec(select(Role).where(Role.name == role_name.value))).first()
            if not existing:
                session.add(Role(name=role_name.value, description=ROLE_DESCRIPTIONS[role_name]))
        await session.commit()

        role: Role = (await session.exec(select(Role).where(Role.name == RoleName.ADMIN.value))).one()

        user_statement = await session.exec(select(User).where(User.username == settings.FIRST_SUPERUSER))
        user: User | None = user_statement.first()
        if not user:
            user_service = UserService(
                user_repository=PostgresUserRepository(session=session),
                role_repository=PostgresRoleRepository(session=session),
                refresh_token_repository=PostgresRefreshTokenRepository(session=session)
            )
            user_in = UserCreate(
                username=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                role_id=role.id
            )
            await user_service.create_user(user_in, must_change_password=False)
