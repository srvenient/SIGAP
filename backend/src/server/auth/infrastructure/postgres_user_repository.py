from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.auth.domain.user.user import User
from src.server.auth.domain.user.user_repository import UserRepository


class PostgresUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, user_id: UUID) -> User | None:
        user: User | None = await self.session.get(User, user_id)
        return user

    async def find_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def find_all(self, skip: int = 0, limit: int = 50) -> list[User]:
        result = await self.session.execute(
            select(User).order_by(User.created_at).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(User))
        return result.scalar_one()

    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user_id: UUID, user_data) -> User | None:
        user: User | None = await self.find_by_id(user_id)
        if user is None:
            return None
        for key, value in user_data.items():
            setattr(user, key, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user_id: UUID):
        user: User | None = await self.find_by_id(user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()

    async def delete_and_retrieve(self, user_id: UUID) -> User | None:
        user: User | None = await self.find_by_id(user_id)
        if user is None:
            return None
        await self.session.delete(user)
        await self.session.commit()
        return user
