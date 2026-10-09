from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.auth.domain.role.role import Role
from src.server.auth.domain.role.role_repository import RoleRepository


class PostgresRoleRepository(RoleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, role_id: str) -> Role | None:
        role: Role | None = await self.session.get(Role, role_id)
        return role

    async def find_by_name(self, role_name: str) -> Role | None:
        statement = select(Role).where(Role.name == role_name)
        result = await self.session.execute(statement)
        role = result.scalar_one_or_none()
        return role

    async def find_all(self) -> list[Role]:
        statement = select(Role)
        result = await self.session.execute(statement)
        roles = result.scalars().all()
        return [role for role in roles]

    async def save(self, role) -> Role:
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def update(self, role_id: str, role_data) -> Role | None:
        role = await self.find_by_id(role_id)
        if not role:
            return None
        for key, value in role_data.items():
            setattr(role, key, value)
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def delete(self, role_id: str):
        role: Role | None = await self.find_by_id(role_id)
        if role:
            await self.session.delete(role)
            await self.session.commit()

    async def delete_and_retrieve(self, role_id: str) -> Role | None:
        role = await self.find_by_id(role_id)
        if role is None:
            return None
        await self.session.delete(role)
        await self.session.commit()
        return role
