from abc import abstractmethod, ABC

from src.server.auth.domain.role.role import Role


class RoleRepository(ABC):
    @abstractmethod
    async def find_by_id(self, role_id: str) -> Role | None:
        raise NotImplementedError

    @abstractmethod
    async def find_by_name(self, role_name: str) -> Role | None:
        raise NotImplementedError

    @abstractmethod
    async def find_all(self) -> list[Role]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, role) -> Role:
        raise NotImplementedError

    @abstractmethod
    async def update(self, role_id: str, role_data) -> Role | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, role_id: str):
        raise NotImplementedError

    @abstractmethod
    async def delete_and_retrieve(self, role_id: str) -> Role | None:
        raise NotImplementedError
