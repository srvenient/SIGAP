from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from src.server.shared.domain.errors import DomainError
from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.shared.infrastructure.sql_types import EnumStr
from src.server.transaction.domain.plate import VehicleType


class TariffNotFound(DomainError):
    status_code = 404
    detail = "No hay tarifa configurada para este tipo de vehículo"


class Tariff(SQLModel, table=True):
    """Tarifa vigente; la anterior se conserva en TariffHistory antes de cada cambio."""

    __tablename__ = "tariffs"
    __table_args__ = (UniqueConstraint("parking_lot_id", "vehicle_type", name="uq_tariff_lot_vehicle"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    parking_lot_id: UUID = Field(foreign_key="parking_lots.id", index=True)
    vehicle_type: VehicleType = Field(sa_type=EnumStr(VehicleType, 20))
    hourly_rate: Decimal = Field(sa_type=Numeric(12, 2))
    fraction_rate: Decimal = Field(sa_type=Numeric(12, 2))
    fraction_minutes: int
    full_rate: Decimal = Field(sa_type=Numeric(12, 2))
    full_rate_after_minutes: int = Field(default=300)
    updated_at: datetime = Field(
        default_factory=get_localized_now,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": get_localized_now},
    )

    def snapshot(self) -> dict[str, Any]:
        return {
            "vehicle_type": VehicleType(self.vehicle_type).value,
            "hourly_rate": float(self.hourly_rate),
            "fraction_rate": float(self.fraction_rate),
            "fraction_minutes": self.fraction_minutes,
            "full_rate": float(self.full_rate),
            "full_rate_after_minutes": self.full_rate_after_minutes,
        }


class TariffPublic(SQLModel):
    id: UUID
    vehicle_type: VehicleType
    hourly_rate: float
    fraction_rate: float
    fraction_minutes: int
    full_rate: float
    full_rate_after_minutes: int
    updated_at: datetime


class TariffUpdate(SQLModel):
    hourly_rate: Decimal = Field(gt=0, le=10_000_000, decimal_places=2)
    fraction_rate: Decimal = Field(gt=0, le=10_000_000, decimal_places=2)
    fraction_minutes: int = Field(ge=1, le=59)
    full_rate: Decimal = Field(gt=0, le=10_000_000, decimal_places=2)
    full_rate_after_minutes: int = Field(ge=1, le=720)


class TariffHistory(SQLModel, table=True):
    """Solo inserción: un trigger de Postgres rechaza UPDATE y DELETE (HU-14)."""

    __tablename__ = "tariff_history"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    parking_lot_id: UUID = Field(foreign_key="parking_lots.id", index=True)
    vehicle_type: VehicleType = Field(sa_type=EnumStr(VehicleType, 20), index=True)
    previous_config: dict[str, Any] = Field(sa_type=JSONB)
    new_config: dict[str, Any] = Field(sa_type=JSONB)
    changed_by_id: UUID | None = None
    changed_by_username: str = Field(max_length=80)
    changed_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True), index=True
    )


class TariffHistoryPublic(SQLModel):
    id: UUID
    vehicle_type: VehicleType
    previous_config: dict[str, Any]
    new_config: dict[str, Any]
    changed_by_username: str
    changed_at: datetime


class TariffHistoriesPublic(SQLModel):
    data: list[TariffHistoryPublic]
    count: int
