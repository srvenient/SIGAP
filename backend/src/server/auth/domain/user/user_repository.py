from abc import ABC, abstractmethod
from uuid import UUID

from src.server.auth.domain.user.user import User


class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 50) -> list[User]: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def count_active_by_role(self, role_id: UUID) -> int: ...

    @abstractmethod
    async def save(self, user: User) -> User: ...

    @abstractmethod
    async def update(self, user_id: UUID, user_data) -> User | None: ...

    @abstractmethod
    async def delete(self, user_id: UUID): ...

    @abstractmethod
    async def delete_and_retrieve(self, user_id: UUID) -> User | None: ...
