from abc import abstractmethod, ABC
from uuid import UUID

from src.server.auth.domain.role.role import Role


class RoleRepository(ABC):
    @abstractmethod
    async def find_by_id(self, role_id: UUID) -> Role | None: ...

    @abstractmethod
    async def find_by_name(self, role_name: str) -> Role | None: ...

    @abstractmethod
    async def find_all(self) -> list[Role]: ...

    @abstractmethod
    async def save(self, role) -> Role: ...

    @abstractmethod
    async def update(self, role_id: UUID, role_data) -> Role | None: ...

    @abstractmethod
    async def delete(self, role_id: UUID): ...

    @abstractmethod
    async def delete_and_retrieve(self, role_id: UUID) -> Role | None: ...
