from abc import ABC, abstractmethod
from uuid import UUID

from src.server.auth.domain.user.user import User


class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def update(self, user_id: UUID, user_data) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, user_id: UUID):
        raise NotImplementedError

    @abstractmethod
    async def delete_and_retrieve(self, user_id: UUID) -> User | None:
        raise NotImplementedError
