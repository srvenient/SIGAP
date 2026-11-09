from uuid import UUID

from src.server.audit.application.audit_recorder import AuditRecorder
from src.server.audit.domain.audit_log import SYSTEM, Actor, AuditAction
from src.server.parking.domain.parking_lot_repository import ParkingLotRepository
from src.server.ticket.domain.ticket import (
    InvalidTicketTransition,
    Ticket,
    TicketClose,
    TicketCreate,
    TicketHistory,
    TicketNotes,
    TicketNotFound,
    TicketOrigin,
    TicketStatus,
)
from src.server.ticket.domain.ticket_repository import TicketRepository
from src.server.transaction.domain.transaction import TransactionNotFound
from src.server.transaction.domain.transaction_repository import TransactionRepository

_TAKEABLE = (TicketStatus.PENDING, TicketStatus.NOT_SOLVED)
_CLOSING = (TicketStatus.SOLVED, TicketStatus.NOT_SOLVED)


class TicketService:
    def __init__(
            self,
            repository: TicketRepository,
            parking_lots: ParkingLotRepository,
            transactions: TransactionRepository,
            audit: AuditRecorder,
    ):
        self.repository = repository
        self.parking_lots = parking_lots
        self.transactions = transactions
        self.audit = audit

    async def create_manual(self, data: TicketCreate, actor: Actor) -> Ticket:
        if data.transaction_id and await self.transactions.find_by_id(data.transaction_id) is None:
            raise TransactionNotFound

        lot = await self.parking_lots.get_default()
        ticket = Ticket(
            parking_lot_id=lot.id,
            origin=TicketOrigin.MANUAL,
            component=data.component.strip(),
            description=data.description.strip(),
            transaction_id=data.transaction_id,
            created_by_id=actor.user_id,
            created_by_username=actor.label,
        )
        self._register_creation(ticket, actor)
        await self.repository.commit()
        return ticket

    async def open_automatic(self, event) -> Ticket | None:
        """Crea el ticket de un evento técnico (HU-24). El llamador confirma la transacción."""
        if await self.repository.find_open(event.component, event.error_code):
            return None  # el problema ya tiene un ticket sin resolver

        ticket = Ticket(
            parking_lot_id=event.parking_lot_id,
            origin=TicketOrigin.AUTOMATIC,
            component=event.component,
            error_code=event.error_code,
            description=event.description,
            transaction_id=event.transaction_id,
            technical_event_id=event.id,
            created_by_username=SYSTEM.label,
        )
        self._register_creation(ticket, SYSTEM)
        return ticket

    def _register_creation(self, ticket: Ticket, actor: Actor) -> None:
        self.repository.add(ticket)
        self.repository.add(TicketHistory(
            ticket_id=ticket.id,
            to_status=TicketStatus.PENDING,
            user_id=actor.user_id,
            username=actor.label,
            note="Ticket creado",
        ))
        self.audit.record(
            AuditAction.TICKET_CREATED, actor, "ticket", ticket.id, ticket.component,
            detail={"origen": ticket.origin.value, "codigo": ticket.error_code},
        )

    async def search(
            self, status: TicketStatus | None, created_by: UUID | None, skip: int, limit: int
    ) -> tuple[list[Ticket], int]:
        return await self.repository.search(status, created_by, skip, limit)

    async def get(self, ticket_id: UUID) -> tuple[Ticket, list[TicketHistory]]:
        ticket = await self.repository.find_by_id(ticket_id)
        if ticket is None:
            raise TicketNotFound
        return ticket, await self.repository.history_of(ticket_id)

    async def _locked(self, ticket_id: UUID) -> Ticket:
        ticket = await self.repository.find_by_id(ticket_id, for_update=True)
        if ticket is None:
            raise TicketNotFound
        return ticket

    def _transition(self, ticket: Ticket, to_status: TicketStatus, actor: Actor, note: str) -> None:
        previous = ticket.status
        ticket.status = to_status
        self.repository.add(ticket)
        self.repository.add(TicketHistory(
            ticket_id=ticket.id,
            from_status=previous,
            to_status=to_status,
            user_id=actor.user_id,
            username=actor.label,
            note=note,
        ))
        self.audit.record(
            AuditAction.TICKET_STATUS_CHANGED, actor, "ticket", ticket.id, ticket.component,
            detail={"anterior": previous.value, "nuevo": to_status.value},
        )

    async def take(self, ticket_id: UUID, actor: Actor) -> Ticket:
        ticket = await self._locked(ticket_id)
        if ticket.status not in _TAKEABLE:
            raise InvalidTicketTransition("Solo se puede tomar un ticket pendiente o no solucionado")

        ticket.assignee_id = actor.user_id
        ticket.assignee_username = actor.label
        self._transition(ticket, TicketStatus.IN_REVIEW, actor, "Inicia la revisión")
        await self.repository.commit()
        return ticket

    async def save_notes(self, ticket_id: UUID, data: TicketNotes) -> Ticket:
        ticket = await self._locked(ticket_id)
        if ticket.status != TicketStatus.IN_REVIEW:
            raise InvalidTicketTransition("Solo se puede registrar información durante la revisión")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(ticket, field, value)
        self.repository.add(ticket)
        await self.repository.commit()
        return ticket

    async def close(self, ticket_id: UUID, data: TicketClose, actor: Actor) -> Ticket:
        if data.status not in _CLOSING:
            raise InvalidTicketTransition("El estado final debe ser solucionado o no solucionado")

        ticket = await self._locked(ticket_id)
        if ticket.status != TicketStatus.IN_REVIEW:
            raise InvalidTicketTransition("Solo se puede cerrar un ticket en revisión")

        ticket.diagnosis = data.diagnosis
        ticket.actions_taken = data.actions_taken
        ticket.result = data.result
        self._transition(ticket, data.status, actor, data.result[:300])
        await self.repository.commit()
        return ticket
