from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import DateTime, Index, Numeric, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field

from src.server.shared.domain.errors import DomainError
from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.transaction.domain.plate import VehicleType, normalize_plate


class TransactionStatus(str, Enum):
    ENTERED = "entered"
    PAID = "paid"
    COMPLETED = "completed"


ACTIVE_STATUSES = (TransactionStatus.ENTERED, TransactionStatus.PAID)


class AlreadyInside(DomainError):
    status_code = 400
    detail = "Ya existe una transacción activa para esta placa"


class ParkingFull(DomainError):
    status_code = 409
    detail = "Parqueadero lleno: no hay cupos disponibles"


class InvalidPlate(DomainError):
    status_code = 422
    detail = "La placa no tiene un formato válido para el tipo de vehículo"


class PaymentPending(DomainError):
    status_code = 402
    detail = "El pago está pendiente. Salida no autorizada."


class NoActiveTransaction(DomainError):
    status_code = 404
    detail = "No existe una transacción activa para esta placa. Salida no autorizada."


class TransactionNotFound(DomainError):
    status_code = 404
    detail = "Transacción no encontrada"


class InvalidTransactionState(DomainError):
    status_code = 409
    detail = "La transacción no está en un estado válido para esta operación"


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"
    __table_args__ = (
        # Garantía en BD de HU-03: una placa no puede tener dos transacciones activas
        Index(
            "uq_transactions_active_plate",
            "plate",
            unique=True,
            postgresql_where=text("status IN ('ENTERED', 'PAID')"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    parking_lot_id: UUID = Field(foreign_key="parking_lots.id", index=True)

    plate: str = Field(index=True, max_length=10, nullable=False)
    vehicle_type: VehicleType = Field(nullable=False)
    status: TransactionStatus = Field(default=TransactionStatus.ENTERED, nullable=False, index=True)

    entry_time: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True), index=True
    )
    # Nulo = se registró el ingreso pero la talanquera aún no confirmó la apertura
    entry_gate_opened_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))
    exit_time: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))

    # Liquidación congelada al confirmar el pago: los cambios de tarifa no la afectan
    total_amount: Optional[Decimal] = Field(default=None, sa_type=Numeric(12, 2))
    billed_minutes: Optional[int] = None
    tariff_snapshot: Optional[dict[str, Any]] = Field(default=None, sa_type=JSONB)
    payment_method: Optional[str] = Field(default=None, max_length=50)
    payment_reference: Optional[str] = Field(default=None, max_length=100)
    paid_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True), index=True)

    manual_intervention: bool = Field(default=False, nullable=False)
    manual_reason: Optional[str] = Field(default=None, max_length=300)

    created_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True)
    )
    updated_at: datetime = Field(
        default_factory=get_localized_now,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": get_localized_now},
    )


class TransactionCreate(SQLModel):
    """Solo lo que aporta la cámara; fecha, estado y parqueadero los pone el sistema (HU-04)."""

    plate: str = Field(min_length=5, max_length=10)
    vehicle_type: VehicleType

    @field_validator("plate", mode="before")
    @classmethod
    def _clean_plate(cls, value: Any) -> Any:
        return normalize_plate(value) if isinstance(value, str) else value


class TransactionPublic(SQLModel):
    id: UUID
    plate: str
    vehicle_type: VehicleType
    status: TransactionStatus
    entry_time: datetime
    exit_time: Optional[datetime] = None
    total_amount: Optional[float] = None
    billed_minutes: Optional[int] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    paid_at: Optional[datetime] = None
    manual_intervention: bool = False
    manual_reason: Optional[str] = None


class TransactionsPublic(SQLModel):
    data: list[TransactionPublic]
    count: int
