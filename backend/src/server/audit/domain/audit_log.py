from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.shared.infrastructure.sql_types import EnumStr


class AuditAction(str, Enum):
    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_COMPLETED = "transaction.completed"
    PLATE_CORRECTED = "transaction.plate_corrected"
    PAYMENT_APPROVED = "payment.approved"
    PAYMENT_FAILED = "payment.failed"
    GATE_OPENED = "gate.opened"
    GATE_OPEN_FAILED = "gate.open_failed"
    GATE_OPEN_REQUESTED = "gate.open_requested"
    TARIFF_UPDATED = "tariff.updated"
    PARKING_UPDATED = "parking.updated"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_PASSWORD_RESET = "user.password_reset"
    USER_UNLOCKED = "user.unlocked"
    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    ALERT_RESOLVED = "alert.resolved"
    ALERT_DISMISSED = "alert.dismissed"
    TICKET_CREATED = "ticket.created"
    TICKET_STATUS_CHANGED = "ticket.status_changed"


class AuditResult(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class Actor:
    """Quién ejecuta una acción: un usuario, el sistema o un conductor sin cuenta."""

    label: str
    user_id: UUID | None = None

    @classmethod
    def of(cls, user) -> "Actor":
        return cls(label=user.username, user_id=user.id)


SYSTEM = Actor("sistema")
DRIVER = Actor("conductor")


class AuditLog(SQLModel, table=True):
    """Sin FK a users: el registro debe conservarse tal como se generó (HU-28)."""

    __tablename__ = "audit_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    actor_user_id: UUID | None = Field(default=None, index=True)
    actor_label: str = Field(max_length=80, index=True)
    action: AuditAction = Field(sa_type=EnumStr(AuditAction), index=True)
    entity_type: str = Field(max_length=40)
    entity_id: str | None = Field(default=None, max_length=64)
    entity_label: str | None = Field(default=None, max_length=120)
    result: AuditResult = Field(sa_type=EnumStr(AuditResult, 10))
    detail: dict[str, Any] = Field(default_factory=dict, sa_type=JSONB)
    created_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True), index=True
    )


class AuditLogPublic(SQLModel):
    id: UUID
    actor_user_id: UUID | None
    actor_label: str
    action: AuditAction
    entity_type: str
    entity_id: str | None
    entity_label: str | None
    result: AuditResult
    detail: dict[str, Any]
    created_at: datetime


class AuditLogsPublic(SQLModel):
    data: list[AuditLogPublic]
    count: int
