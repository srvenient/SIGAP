from datetime import datetime

from src.server.audit.application.audit_recorder import AuditRecorder
from src.server.audit.domain.audit_log import Actor, AuditAction
from src.server.parking.domain.parking_lot_repository import ParkingLotRepository
from src.server.tariff.domain.tariff import Tariff, TariffHistory, TariffNotFound, TariffUpdate
from src.server.tariff.domain.tariff_repository import TariffRepository
from src.server.transaction.domain.plate import VehicleType


class TariffService:
    def __init__(
            self,
            repository: TariffRepository,
            parking_lots: ParkingLotRepository,
            audit: AuditRecorder,
    ):
        self.repository = repository
        self.parking_lots = parking_lots
        self.audit = audit

    async def list_current(self) -> list[Tariff]:
        lot = await self.parking_lots.get_default()
        return await self.repository.list_current(lot.id)

    async def get_current(self, vehicle_type: VehicleType) -> Tariff:
        lot = await self.parking_lots.get_default()
        tariff = await self.repository.find_current(lot.id, vehicle_type)
        if tariff is None:
            raise TariffNotFound
        return tariff

    async def update(self, vehicle_type: VehicleType, data: TariffUpdate, actor: Actor) -> Tariff:
        tariff = await self.get_current(vehicle_type)
        previous = tariff.snapshot()

        for field, value in data.model_dump().items():
            setattr(tariff, field, value)
        current = tariff.snapshot()
        if current == previous:
            return tariff

        self.repository.add_history(TariffHistory(
            parking_lot_id=tariff.parking_lot_id,
            vehicle_type=vehicle_type,
            previous_config=previous,
            new_config=current,
            changed_by_id=actor.user_id,
            changed_by_username=actor.label,
        ))
        self.audit.record(
            AuditAction.TARIFF_UPDATED, actor, "tariff", tariff.id, vehicle_type.value,
            detail={"anterior": previous, "nuevo": current},
        )
        return await self.repository.save(tariff)

    async def history(
            self,
            vehicle_type: VehicleType | None,
            start: datetime | None,
            end: datetime | None,
            skip: int,
            limit: int,
    ) -> tuple[list[TariffHistory], int]:
        return await self.repository.search_history(vehicle_type, start, end, skip, limit)
