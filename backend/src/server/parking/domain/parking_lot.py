from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel

from src.server.shared.domain.errors import DomainError
from src.server.shared.infrastructure.providers.system_clock import get_localized_now

# Hoy opera una sola sede. Para varias sedes basta con resolver este id por petición:
# todas las tablas operativas ya tienen parking_lot_id.
DEFAULT_PARKING_LOT_ID = UUID("00000000-0000-4000-8000-000000000001")


class ParkingLotNotFound(DomainError):
    status_code = 500
    detail = "El parqueadero no está configurado"


class ParkingLot(SQLModel, table=True):
    __tablename__ = "parking_lots"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=120)
    address: str | None = Field(default=None, max_length=200)
    capacity: int = Field(default=50, ge=1)
    gate_open_seconds: int = Field(default=3, ge=1, le=60)
    created_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True)
    )
    updated_at: datetime = Field(
        default_factory=get_localized_now,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": get_localized_now},
    )


class ParkingLotPublic(SQLModel):
    id: UUID
    name: str
    address: str | None
    capacity: int
    gate_open_seconds: int


class ParkingLotUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=200)
    capacity: int | None = Field(default=None, ge=1, le=100000)
    gate_open_seconds: int | None = Field(default=None, ge=1, le=60)


class Occupancy(BaseModel):
    capacity: int
    occupied: int
    available: int
    percentage: float

    @classmethod
    def of(cls, capacity: int, occupied: int) -> "Occupancy":
        return cls(
            capacity=capacity,
            occupied=occupied,
            available=max(0, capacity - occupied),
            percentage=round(occupied * 100 / capacity, 1) if capacity else 0.0,
        )
