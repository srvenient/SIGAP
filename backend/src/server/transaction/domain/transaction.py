from datetime import datetime
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import DateTime
from sqlmodel import SQLModel, Field

from src.server.shared.infrastructure.providers.system_clock import get_localized_now


class VehicleType(str, Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    UNKNOWN = "unknown"


class TransactionStatus(str, Enum):
    ENTERED = "entered"
    PAID = "paid"
    PROCESSING_PAYMENT = "processing_payment"
    COMPLETED = "completed"


class TransactionBase(SQLModel):
    plate: str = Field(index=True, min_length=5, max_length=10, nullable=False)
    vehicle_type: VehicleType = Field(nullable=False)
    status: TransactionStatus = Field(default=TransactionStatus.ENTERED, nullable=False)

    parking_lot_id: Optional[UUID] = Field(default=None, nullable=True)

    total_amount: Optional[float] = Field(default=None, nullable=True)
    payment_method: Optional[str] = Field(default=None, max_length=50, nullable=True)
    payment_reference: Optional[str] = Field(default=None, max_length=100, nullable=True)

    manual_intervention: bool = Field(default=False, nullable=False)


class TransactionCreate(TransactionBase):
    @field_validator("plate")
    @classmethod
    def _clean_plate(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("La placa debe ser un texto")

        value = "".join(value.split()).upper().replace("-", "")

        if not value.isalnum():
            raise ValueError("La placa solo puede contener letras y números")

        return value


class TransactionUpdate(SQLModel):
    status: Optional[TransactionStatus] = None
    total_amount: Optional[float] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    manual_intervention: Optional[bool] = None
    # No se permite actualizar la placa ni la hora de ingreso por seguridad.


class Transaction(TransactionBase, table=True):
    __tablename__ = "transactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # El registro de la fecha/hora de ingreso se toma automáticamente
    entry_time: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True)
    )

    # Se actualiza cuando la talanquera de salida se abre exitosamente
    exit_time: Optional[datetime] = Field(
        default=None, sa_type=DateTime(timezone=True)
    )

    created_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True)
    )
    updated_at: datetime = Field(
        default_factory=get_localized_now,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": get_localized_now},
    )


class TransactionPublic(TransactionBase):
    id: UUID
    entry_time: datetime
    exit_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TransactionsPublic(SQLModel):
    data: list[TransactionPublic]
    count: int
