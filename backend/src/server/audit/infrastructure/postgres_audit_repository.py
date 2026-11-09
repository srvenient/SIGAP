from datetime import datetime
from typing import Literal

from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.audit.domain.audit_log import AuditAction, AuditLog
from src.server.audit.domain.audit_repository import AuditRepository


class PostgresAuditRepository(AuditRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, entry: AuditLog) -> None:
        self.session.add(entry)

    async def commit(self) -> None:
        await self.session.commit()

    async def search(
            self,
            action: AuditAction | None,
            username: str | None,
            start: datetime | None,
            end: datetime | None,
            order: Literal["asc", "desc"],
            skip: int,
            limit: int,
    ) -> tuple[list[AuditLog], int]:
        conditions = []
        if action:
            conditions.append(col(AuditLog.action) == action)
        if username:
            conditions.append(col(AuditLog.actor_label).icontains(username, autoescape=True))
        if start:
            conditions.append(col(AuditLog.created_at) >= start)
        if end:
            conditions.append(col(AuditLog.created_at) < end)

        ordering = col(AuditLog.created_at).asc() if order == "asc" else col(AuditLog.created_at).desc()
        rows = await self.session.exec(
            select(AuditLog).where(*conditions).order_by(ordering).offset(skip).limit(limit)
        )
        total = await self.session.exec(select(func.count()).select_from(AuditLog).where(*conditions))
        return list(rows.all()), total.one()
