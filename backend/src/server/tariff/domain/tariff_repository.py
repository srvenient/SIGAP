from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.server.tariff.domain.tariff import Tariff, TariffHistory
from src.server.transaction.domain.plate import VehicleType


class TariffRepository(ABC):
    @abstractmethod
    async def list_current(self, parking_lot_id: UUID) -> list[Tariff]: ...

    @abstractmethod
    async def find_current(self, parking_lot_id: UUID, vehicle_type: VehicleType) -> Tariff | None: ...

    @abstractmethod
    def add_history(self, entry: TariffHistory) -> None: ...

    @abstractmethod
    async def save(self, tariff: Tariff) -> Tariff: ...

    @abstractmethod
    async def search_history(
            self,
            vehicle_type: VehicleType | None,
            start: datetime | None,
            end: datetime | None,
            skip: int,
            limit: int,
    ) -> tuple[list[TariffHistory], int]: ...
