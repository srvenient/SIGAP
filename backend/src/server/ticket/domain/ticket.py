from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel

from src.server.shared.domain.errors import DomainError
from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.shared.infrastructure.sql_types import EnumStr


class TicketStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    SOLVED = "solved"
    NOT_SOLVED = "not_solved"


class TicketOrigin(str, Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"


OPEN_STATUSES = (TicketStatus.PENDING, TicketStatus.IN_REVIEW)


class TicketNotFound(DomainError):
    status_code = 404
    detail = "Ticket no encontrado"


class InvalidTicketTransition(DomainError):
    status_code = 409
    detail = "El ticket no puede pasar a ese estado"


class Ticket(SQLModel, table=True):
    __tablename__ = "tickets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    parking_lot_id: UUID = Field(foreign_key="parking_lots.id", index=True)
    origin: TicketOrigin = Field(sa_type=EnumStr(TicketOrigin, 20))
    status: TicketStatus = Field(default=TicketStatus.PENDING, sa_type=EnumStr(TicketStatus, 20), index=True)
    assigned_role: str = Field(default="support", max_length=20)

    component: str = Field(max_length=80, index=True)
    error_code: str | None = Field(default=None, max_length=40)
    description: str = Field(max_length=1000)
    transaction_id: UUID | None = Field(default=None, foreign_key="transactions.id")
    technical_event_id: UUID | None = Field(default=None, foreign_key="technical_events.id")

    created_by_id: UUID | None = Field(default=None, index=True)
    created_by_username: str = Field(max_length=80)
    assignee_id: UUID | None = None
    assignee_username: str | None = Field(default=None, max_length=80)

    diagnosis: str | None = Field(default=None, max_length=2000)
    actions_taken: str | None = Field(default=None, max_length=2000)
    result: str | None = Field(default=None, max_length=2000)

    created_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True), index=True
    )
    updated_at: datetime = Field(
        default_factory=get_localized_now,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": get_localized_now},
    )


class TicketHistory(SQLModel, table=True):
    """Solo inserción: un trigger de Postgres rechaza UPDATE y DELETE (HU-25)."""

    __tablename__ = "ticket_history"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ticket_id: UUID = Field(foreign_key="tickets.id", index=True)
    from_status: TicketStatus | None = Field(default=None, sa_type=EnumStr(TicketStatus, 20))
    to_status: TicketStatus = Field(sa_type=EnumStr(TicketStatus, 20))
    user_id: UUID | None = None
    username: str = Field(max_length=80)
    note: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True)
    )


class TicketCreate(BaseModel):
    component: str = PydanticField(min_length=2, max_length=80)
    description: str = PydanticField(min_length=5, max_length=1000)
    transaction_id: UUID | None = None


class TicketNotes(BaseModel):
    diagnosis: str | None = PydanticField(default=None, max_length=2000)
    actions_taken: str | None = PydanticField(default=None, max_length=2000)
    result: str | None = PydanticField(default=None, max_length=2000)


class TicketClose(BaseModel):
    status: TicketStatus
    diagnosis: str = PydanticField(min_length=3, max_length=2000)
    actions_taken: str = PydanticField(min_length=3, max_length=2000)
    result: str = PydanticField(min_length=3, max_length=2000)


class TicketPublic(SQLModel):
    id: UUID
    origin: TicketOrigin
    status: TicketStatus
    assigned_role: str
    component: str
    error_code: str | None
    description: str
    transaction_id: UUID | None
    technical_event_id: UUID | None
    created_by_username: str
    assignee_username: str | None
    diagnosis: str | None
    actions_taken: str | None
    result: str | None
    created_at: datetime
    updated_at: datetime


class TicketHistoryPublic(SQLModel):
    from_status: TicketStatus | None
    to_status: TicketStatus
    username: str
    note: str | None
    created_at: datetime


class TicketDetail(TicketPublic):
    history: list[TicketHistoryPublic] = []


class TicketsPublic(SQLModel):
    data: list[TicketPublic]
    count: int
