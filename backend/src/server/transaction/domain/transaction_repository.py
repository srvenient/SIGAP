from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional, List

from src.server.transaction.domain.transaction import Transaction


class TransactionRepository(ABC):
    @abstractmethod
    async def find_by_id(self, transaction_id: UUID) -> Optional[Transaction]: ...

    @abstractmethod
    async def find_active_by_plate(self, plate: str) -> Optional[Transaction]: ...

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 50) -> List[Transaction]: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def save(self, transaction: Transaction) -> Transaction: ...

    @abstractmethod
    async def update(self, transaction_id: UUID, transaction_data: dict) -> Optional[Transaction]: ...
