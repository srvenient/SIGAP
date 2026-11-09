from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.server.audit.domain.audit_log import Actor
from src.server.auth.api.deps import OperatorOrSupportDep, OperatorUserDep, SupportUserDep
from src.server.auth.domain.role.role import RoleName
from src.server.shared.api.deps import SessionDep
from src.server.ticket.application.ticket_service import TicketService
from src.server.ticket.domain.ticket import (
    TicketClose,
    TicketCreate,
    TicketDetail,
    TicketHistoryPublic,
    TicketNotes,
    TicketNotFound,
    TicketPublic,
    TicketsPublic,
    TicketStatus,
)
from src.server.wiring import build_ticket_service


def _service(session: SessionDep) -> TicketService:
    return build_ticket_service(session)


ServiceDep = Annotated[TicketService, Depends(_service)]

ticket_router = APIRouter(prefix="/tickets", tags=["Tickets"])


def _only_own_tickets(user) -> bool:
    return user.role.name == RoleName.OPERATOR.value


@ticket_router.post("", response_model=TicketPublic, status_code=status.HTTP_201_CREATED)
async def create_ticket(body: TicketCreate, operator: OperatorUserDep, service: ServiceDep):
    return await service.create_manual(body, Actor.of(operator))


@ticket_router.get("", response_model=TicketsPublic)
async def list_tickets(
        user: OperatorOrSupportDep,
        service: ServiceDep,
        ticket_status: TicketStatus | None = Query(default=None, alias="status"),
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
):
    created_by = user.id if _only_own_tickets(user) else None
    rows, count = await service.search(ticket_status, created_by, skip, limit)
    return TicketsPublic(data=[TicketPublic.model_validate(r) for r in rows], count=count)


@ticket_router.get("/{ticket_id}", response_model=TicketDetail)
async def ticket_detail(ticket_id: UUID, user: OperatorOrSupportDep, service: ServiceDep):
    ticket, history = await service.get(ticket_id)
    if _only_own_tickets(user) and ticket.created_by_id != user.id:
        raise TicketNotFound  # 404: no se revela la existencia de tickets ajenos
    return TicketDetail(
        **TicketPublic.model_validate(ticket).model_dump(),
        history=[TicketHistoryPublic.model_validate(h) for h in history],
    )


@ticket_router.post("/{ticket_id}/take", response_model=TicketPublic)
async def take_ticket(ticket_id: UUID, support: SupportUserDep, service: ServiceDep):
    return await service.take(ticket_id, Actor.of(support))


@ticket_router.patch("/{ticket_id}/notes", response_model=TicketPublic)
async def save_notes(ticket_id: UUID, body: TicketNotes, _: SupportUserDep, service: ServiceDep):
    return await service.save_notes(ticket_id, body)


@ticket_router.post("/{ticket_id}/close", response_model=TicketPublic)
async def close_ticket(ticket_id: UUID, body: TicketClose, support: SupportUserDep, service: ServiceDep):
    return await service.close(ticket_id, body, Actor.of(support))
