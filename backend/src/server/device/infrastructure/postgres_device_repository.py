from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.device.domain.device import (
    CommandStatus,
    Device,
    DeviceStatus,
    Gate,
    GateCommand,
    GateDisplay,
    TechnicalEvent,
)
from src.server.device.domain.device_repository import DeviceRepository


class PostgresDeviceRepository(DeviceRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_devices(self, parking_lot_id: UUID) -> list[Device]:
        result = await self.session.exec(select(Device).where(Device.parking_lot_id == parking_lot_id))
        return list(result.all())

    async def lock_devices(self, parking_lot_id: UUID) -> list[Device]:
        result = await self.session.exec(
            select(Device).where(Device.parking_lot_id == parking_lot_id)
            .with_for_update().execution_options(populate_existing=True)
        )
        return list(result.all())

    async def lock_stale(self, cutoff: datetime) -> list[Device]:
        result = await self.session.exec(
            select(Device).where(
                col(Device.last_report_at).is_not(None),
                col(Device.last_report_at) < cutoff,
                Device.reported_status != DeviceStatus.NO_COMMUNICATION,
            ).with_for_update(skip_locked=True)
        )
        return list(result.all())

    def add(self, entity: Device | GateCommand | GateDisplay | TechnicalEvent) -> None:
        self.session.add(entity)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def list_events(self, skip: int, limit: int) -> tuple[list[TechnicalEvent], int]:
        rows = await self.session.exec(
            select(TechnicalEvent).order_by(col(TechnicalEvent.created_at).desc()).offset(skip).limit(limit)
        )
        total = await self.session.exec(select(func.count()).select_from(TechnicalEvent))
        return list(rows.all()), total.one()

    async def find_command(self, command_id: UUID) -> GateCommand | None:
        return await self.session.get(GateCommand, command_id, with_for_update=True, populate_existing=True)

    async def lock_open_commands(self, parking_lot_id: UUID) -> list[GateCommand]:
        result = await self.session.exec(
            select(GateCommand).where(
                GateCommand.parking_lot_id == parking_lot_id,
                col(GateCommand.status).in_([CommandStatus.PENDING, CommandStatus.SENT]),
            ).order_by(col(GateCommand.created_at)).with_for_update()
        )
        return list(result.all())

    async def recent_commands(self, limit: int) -> list[GateCommand]:
        result = await self.session.exec(
            select(GateCommand).order_by(col(GateCommand.created_at).desc()).limit(limit)
        )
        return list(result.all())

    async def find_display(self, parking_lot_id: UUID, gate: Gate) -> GateDisplay | None:
        result = await self.session.exec(
            select(GateDisplay).where(GateDisplay.parking_lot_id == parking_lot_id, GateDisplay.gate == gate)
        )
        return result.first()
