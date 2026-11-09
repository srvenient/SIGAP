from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import DateTime, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from src.server.shared.domain.errors import DomainError
from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.shared.infrastructure.sql_types import EnumStr
from src.server.transaction.domain.plate import VehicleType
from src.server.transaction.domain.transaction import TransactionStatus


class PaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentNotFound(DomainError):
    status_code = 404
    detail = "Referencia de pago no encontrada"


class NothingToPay(DomainError):
    status_code = 404
    detail = "No hay un vehículo con esa placa pendiente de pago"


class AlreadyPaid(DomainError):
    status_code = 409
    detail = "Esta transacción ya fue pagada"


class InvalidPaymentMethod(DomainError):
    status_code = 422
    detail = "Medio de pago no disponible"


class PaymentAttempt(SQLModel, table=True):
    """Cada intento queda registrado; la transacción sigue en Ingresado hasta que uno se apruebe."""

    __tablename__ = "payment_attempts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    transaction_id: UUID = Field(foreign_key="transactions.id", index=True)
    reference: str = Field(unique=True, index=True, max_length=64)
    gateway: str = Field(max_length=30)
    method: str = Field(max_length=30)
    amount: Decimal = Field(sa_type=Numeric(12, 2))
    billed_minutes: int
    tariff_snapshot: dict[str, Any] = Field(sa_type=JSONB)
    status: PaymentStatus = Field(
        default=PaymentStatus.PENDING, sa_type=EnumStr(PaymentStatus, 20), index=True
    )
    failure_reason: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True), index=True
    )
    resolved_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class PaymentAttemptPublic(SQLModel):
    id: UUID
    reference: str
    gateway: str
    method: str
    amount: float
    status: PaymentStatus
    failure_reason: str | None
    created_at: datetime
    resolved_at: datetime | None


class PaymentMethod(BaseModel):
    code: str
    label: str


class PaymentMethods(BaseModel):
    methods: list[PaymentMethod]
    simulated: bool


class Quote(BaseModel):
    plate: str
    vehicle_type: VehicleType
    status: TransactionStatus
    entry_time: datetime
    minutes: int
    amount: float
    charge_mode: str | None = None
    periods: int = 1


class PaymentStart(BaseModel):
    plate: str = PydanticField(min_length=5, max_length=10)
    method: str = PydanticField(min_length=1, max_length=30)


class PaymentState(BaseModel):
    reference: str
    plate: str
    method: str
    amount: float
    status: PaymentStatus
    failure_reason: str | None = None
    expires_at: datetime
    simulated: bool
