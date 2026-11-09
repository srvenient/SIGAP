from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import DateTime, LargeBinary
from sqlmodel import Field, SQLModel

from src.server.device.domain.device import Gate
from src.server.shared.domain.errors import DomainError
from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.shared.infrastructure.sql_types import EnumStr


class AlertType(str, Enum):
    PLATE_UNREADABLE = "plate_unreadable"
    PAYMENT_PENDING = "payment_pending"
    NO_ACTIVE_TRANSACTION = "no_active_transaction"


class AlertStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AlertNotFound(DomainError):
    status_code = 404
    detail = "Alerta no encontrada"


class AlertAlreadyClosed(DomainError):
    status_code = 409
    detail = "Esta alerta ya fue atendida"


class OperationAlert(SQLModel, table=True):
    __tablename__ = "operation_alerts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    parking_lot_id: UUID = Field(foreign_key="parking_lots.id", index=True)
    gate: Gate = Field(sa_type=EnumStr(Gate, 10))
    alert_type: AlertType = Field(sa_type=EnumStr(AlertType, 30))
    status: AlertStatus = Field(default=AlertStatus.PENDING, sa_type=EnumStr(AlertStatus, 20), index=True)
    plate_read: str | None = Field(default=None, max_length=10, index=True)
    message: str = Field(max_length=200)
    has_snapshot: bool = Field(default=False)
    transaction_id: UUID | None = Field(default=None, foreign_key="transactions.id")
    resolved_by_id: UUID | None = None
    resolved_by_username: str | None = Field(default=None, max_length=80)
    resolution_note: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True), index=True
    )
    resolved_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class AlertSnapshot(SQLModel, table=True):
    """En tabla aparte para no cargar imágenes en los listados. Se borra al atender la alerta."""

    __tablename__ = "alert_snapshots"

    alert_id: UUID = Field(foreign_key="operation_alerts.id", primary_key=True)
    image: bytes = Field(sa_type=LargeBinary)


class AlertIn(BaseModel):
    gate: Gate
    alert_type: AlertType
    message: str = PydanticField(min_length=1, max_length=200)
    plate_read: str | None = PydanticField(default=None, max_length=10)
    snapshot_b64: str | None = PydanticField(default=None, max_length=400_000)


class AlertPublic(SQLModel):
    id: UUID
    gate: Gate
    alert_type: AlertType
    status: AlertStatus
    plate_read: str | None
    message: str
    has_snapshot: bool
    transaction_id: UUID | None
    resolved_by_username: str | None
    resolution_note: str | None
    created_at: datetime
    resolved_at: datetime | None


class ManualPlate(BaseModel):
    plate: str = PydanticField(min_length=5, max_length=10)
    reason: str = PydanticField(min_length=3, max_length=300)


class Reason(BaseModel):
    reason: str = PydanticField(min_length=3, max_length=300)
