from uuid import UUID

from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.ticket.domain.ticket import OPEN_STATUSES, Ticket, TicketHistory, TicketStatus
from src.server.ticket.domain.ticket_repository import TicketRepository


class PostgresTicketRepository(TicketRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, ticket_id: UUID, for_update: bool = False) -> Ticket | None:
        return await self.session.get(Ticket, ticket_id, with_for_update=for_update, populate_existing=for_update)

    async def find_open(self, component: str, error_code: str) -> Ticket | None:
        result = await self.session.exec(
            select(Ticket).where(
                Ticket.component == component,
                Ticket.error_code == error_code,
                col(Ticket.status).in_(OPEN_STATUSES),
            )
        )
        return result.first()

    async def search(
            self, status: TicketStatus | None, created_by: UUID | None, skip: int, limit: int
    ) -> tuple[list[Ticket], int]:
        conditions = []
        if status:
            conditions.append(col(Ticket.status) == status)
        if created_by:
            conditions.append(col(Ticket.created_by_id) == created_by)

        rows = await self.session.exec(
            select(Ticket).where(*conditions).order_by(col(Ticket.created_at).desc()).offset(skip).limit(limit)
        )
        total = await self.session.exec(select(func.count()).select_from(Ticket).where(*conditions))
        return list(rows.all()), total.one()

    async def history_of(self, ticket_id: UUID) -> list[TicketHistory]:
        result = await self.session.exec(
            select(TicketHistory).where(TicketHistory.ticket_id == ticket_id)
            .order_by(col(TicketHistory.created_at))
        )
        return list(result.all())

    def add(self, entity: Ticket | TicketHistory) -> None:
        self.session.add(entity)

    async def commit(self) -> None:
        await self.session.commit()
