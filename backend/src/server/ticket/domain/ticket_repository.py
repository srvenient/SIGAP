from abc import ABC, abstractmethod
from uuid import UUID

from src.server.ticket.domain.ticket import Ticket, TicketHistory, TicketStatus


class TicketRepository(ABC):
    @abstractmethod
    async def find_by_id(self, ticket_id: UUID, for_update: bool = False) -> Ticket | None: ...

    @abstractmethod
    async def find_open(self, component: str, error_code: str) -> Ticket | None: ...

    @abstractmethod
    async def search(
            self, status: TicketStatus | None, created_by: UUID | None, skip: int, limit: int
    ) -> tuple[list[Ticket], int]: ...

    @abstractmethod
    async def history_of(self, ticket_id: UUID) -> list[TicketHistory]: ...

    @abstractmethod
    def add(self, entity: Ticket | TicketHistory) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...
