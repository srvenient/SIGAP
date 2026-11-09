from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.server.transaction.domain.plate import VehicleType
from src.server.transaction.domain.transaction import Transaction, TransactionStatus


@dataclass(frozen=True)
class TransactionFilters:
    plate: str | None = None
    vehicle_type: VehicleType | None = None
    status: TransactionStatus | None = None
    start: datetime | None = None
    end: datetime | None = None


class TransactionRepository(ABC):
    @abstractmethod
    async def find_by_id(self, transaction_id: UUID) -> Transaction | None: ...

    @abstractmethod
    async def find_by_id_for_update(self, transaction_id: UUID) -> Transaction | None: ...

    @abstractmethod
    async def find_active_by_plate(self, plate: str, for_update: bool = False) -> Transaction | None: ...

    @abstractmethod
    async def count_inside(self, parking_lot_id: UUID) -> int: ...

    @abstractmethod
    async def list_inside(self, parking_lot_id: UUID, plate: str | None) -> list[Transaction]: ...

    @abstractmethod
    async def search(
            self, filters: TransactionFilters, skip: int, limit: int
    ) -> tuple[list[Transaction], int]: ...

    @abstractmethod
    async def save(self, transaction: Transaction) -> Transaction: ...
