from abc import ABC, abstractmethod

from src.server.parking.domain.parking_lot import ParkingLot


class ParkingLotRepository(ABC):
    @abstractmethod
    async def get_default(self) -> ParkingLot: ...

    @abstractmethod
    async def get_default_for_update(self) -> ParkingLot:
        """Bloquea la fila hasta el commit para serializar los ingresos y no exceder la capacidad."""

    @abstractmethod
    async def save(self, lot: ParkingLot) -> ParkingLot: ...
