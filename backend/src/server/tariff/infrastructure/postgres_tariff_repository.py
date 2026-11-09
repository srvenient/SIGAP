from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.tariff.domain.tariff import Tariff, TariffHistory
from src.server.tariff.domain.tariff_repository import TariffRepository
from src.server.transaction.domain.plate import VehicleType


class PostgresTariffRepository(TariffRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_current(self, parking_lot_id: UUID) -> list[Tariff]:
        result = await self.session.exec(
            select(Tariff).where(Tariff.parking_lot_id == parking_lot_id).order_by(Tariff.vehicle_type)
        )
        return list(result.all())

    async def find_current(self, parking_lot_id: UUID, vehicle_type: VehicleType) -> Tariff | None:
        result = await self.session.exec(
            select(Tariff).where(Tariff.parking_lot_id == parking_lot_id, Tariff.vehicle_type == vehicle_type)
        )
        return result.first()

    def add_history(self, entry: TariffHistory) -> None:
        self.session.add(entry)

    async def save(self, tariff: Tariff) -> Tariff:
        self.session.add(tariff)
        await self.session.commit()
        await self.session.refresh(tariff)
        return tariff

    async def search_history(
            self,
            vehicle_type: VehicleType | None,
            start: datetime | None,
            end: datetime | None,
            skip: int,
            limit: int,
    ) -> tuple[list[TariffHistory], int]:
        conditions = []
        if vehicle_type:
            conditions.append(col(TariffHistory.vehicle_type) == vehicle_type)
        if start:
            conditions.append(col(TariffHistory.changed_at) >= start)
        if end:
            conditions.append(col(TariffHistory.changed_at) < end)

        rows = await self.session.exec(
            select(TariffHistory).where(*conditions)
            .order_by(col(TariffHistory.changed_at).desc()).offset(skip).limit(limit)
        )
        total = await self.session.exec(select(func.count()).select_from(TariffHistory).where(*conditions))
        return list(rows.all()), total.one()
