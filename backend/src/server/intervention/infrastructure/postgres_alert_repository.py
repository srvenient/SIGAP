from uuid import UUID

from sqlalchemy import delete
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.device.domain.device import Gate
from src.server.intervention.domain.alert import (
    AlertSnapshot,
    AlertStatus,
    AlertType,
    OperationAlert,
)
from src.server.intervention.domain.alert_repository import AlertRepository


class PostgresAlertRepository(AlertRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, alert_id: UUID, for_update: bool = False) -> OperationAlert | None:
        return await self.session.get(
            OperationAlert, alert_id, with_for_update=for_update, populate_existing=for_update
        )

    async def find_pending_duplicate(
            self, alert_type: AlertType, gate: Gate, plate: str | None
    ) -> OperationAlert | None:
        result = await self.session.exec(
            select(OperationAlert).where(
                OperationAlert.alert_type == alert_type,
                OperationAlert.gate == gate,
                OperationAlert.plate_read == plate,
                OperationAlert.status == AlertStatus.PENDING,
            )
        )
        return result.first()

    async def search(self, status: AlertStatus | None, limit: int) -> list[OperationAlert]:
        statement = select(OperationAlert)
        if status:
            statement = statement.where(OperationAlert.status == status)
        result = await self.session.exec(statement.order_by(col(OperationAlert.created_at).desc()).limit(limit))
        return list(result.all())

    async def get_snapshot(self, alert_id: UUID) -> AlertSnapshot | None:
        return await self.session.get(AlertSnapshot, alert_id)

    async def delete_snapshot(self, alert_id: UUID) -> None:
        await self.session.exec(delete(AlertSnapshot).where(col(AlertSnapshot.alert_id) == alert_id))

    def add(self, entity: OperationAlert | AlertSnapshot) -> None:
        self.session.add(entity)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()
