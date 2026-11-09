from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

from src.server.shared.domain.errors import DomainError
from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.shared.infrastructure.sql_types import EnumStr


class Gate(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"


class DeviceCode(str, Enum):
    CAMERA_ENTRY = "camera_entry"
    CAMERA_EXIT = "camera_exit"
    GATE_ENTRY = "gate_entry"
    GATE_EXIT = "gate_exit"


class DeviceKind(str, Enum):
    CAMERA = "camera"
    GATE = "gate"


class DeviceStatus(str, Enum):
    CONNECTED = "connected"
    NO_COMMUNICATION = "no_communication"
    ERROR = "error"


class CommandStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DONE = "done"
    FAILED = "failed"
    EXPIRED = "expired"


class DisplayState(str, Enum):
    IDLE = "idle"
    VALIDATING = "validating"
    GRANTED = "granted"
    DENIED = "denied"
    ERROR = "error"


DEVICE_CATALOG: dict[DeviceCode, tuple[DeviceKind, str]] = {
    DeviceCode.CAMERA_ENTRY: (DeviceKind.CAMERA, "Cámara de ingreso"),
    DeviceCode.CAMERA_EXIT: (DeviceKind.CAMERA, "Cámara de salida"),
    DeviceCode.GATE_ENTRY: (DeviceKind.GATE, "Talanquera de ingreso"),
    DeviceCode.GATE_EXIT: (DeviceKind.GATE, "Talanquera de salida"),
}

GATE_DEVICE = {Gate.ENTRY: DeviceCode.GATE_ENTRY, Gate.EXIT: DeviceCode.GATE_EXIT}


class DeviceNotFound(DomainError):
    status_code = 404
    detail = "Dispositivo no encontrado"


class CommandNotFound(DomainError):
    status_code = 404
    detail = "Orden de apertura no encontrada"


class Device(SQLModel, table=True):
    __tablename__ = "devices"
    __table_args__ = (UniqueConstraint("parking_lot_id", "code", name="uq_device_lot_code"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    parking_lot_id: UUID = Field(foreign_key="parking_lots.id", index=True)
    code: DeviceCode = Field(sa_type=EnumStr(DeviceCode, 30))
    kind: DeviceKind = Field(sa_type=EnumStr(DeviceKind, 20))
    name: str = Field(max_length=80)
    reported_status: DeviceStatus = Field(
        default=DeviceStatus.NO_COMMUNICATION, sa_type=EnumStr(DeviceStatus, 20)
    )
    last_error: str | None = Field(default=None, max_length=300)
    # Último reporte del worker: si envejece, nadie está vigilando este dispositivo
    last_report_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    # Última vez que el dispositivo mismo respondió (HU-22)
    last_seen_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class DevicePublic(BaseModel):
    code: DeviceCode
    kind: DeviceKind
    name: str
    status: DeviceStatus
    last_error: str | None
    last_seen_at: datetime | None


class DeviceReport(BaseModel):
    code: DeviceCode
    status: DeviceStatus
    error: str | None = PydanticField(default=None, max_length=300)


class Heartbeat(BaseModel):
    devices: list[DeviceReport]


class GateCommandOut(BaseModel):
    id: UUID
    gate: Gate


class HeartbeatResponse(BaseModel):
    gate_open_seconds: int
    commands: list[GateCommandOut]


class TechnicalEvent(SQLModel, table=True):
    __tablename__ = "technical_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    parking_lot_id: UUID = Field(foreign_key="parking_lots.id", index=True)
    device_id: UUID | None = Field(default=None, foreign_key="devices.id", index=True)
    component: str = Field(max_length=80)
    error_code: str = Field(max_length=40, index=True)
    description: str = Field(max_length=500)
    transaction_id: UUID | None = Field(default=None, foreign_key="transactions.id")
    created_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True), index=True
    )


class TechnicalEventIn(BaseModel):
    device_code: DeviceCode
    error_code: str = PydanticField(min_length=1, max_length=40)
    description: str = PydanticField(min_length=1, max_length=500)
    transaction_id: UUID | None = None


class TechnicalEventPublic(SQLModel):
    id: UUID
    component: str
    error_code: str
    description: str
    transaction_id: UUID | None
    created_at: datetime


class GateCommand(SQLModel, table=True):
    """Orden de apertura iniciada por una persona; el worker la recoge en el heartbeat."""

    __tablename__ = "gate_commands"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    parking_lot_id: UUID = Field(foreign_key="parking_lots.id", index=True)
    gate: Gate = Field(sa_type=EnumStr(Gate, 10))
    transaction_id: UUID | None = Field(default=None, foreign_key="transactions.id")
    reason: str = Field(max_length=300)
    requested_by_id: UUID | None = None
    requested_by_username: str = Field(max_length=80)
    status: CommandStatus = Field(default=CommandStatus.PENDING, sa_type=EnumStr(CommandStatus, 20), index=True)
    error: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(
        default_factory=get_localized_now, nullable=False, sa_type=DateTime(timezone=True), index=True
    )
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class GateCommandPublic(SQLModel):
    id: UUID
    gate: Gate
    transaction_id: UUID | None
    reason: str
    requested_by_username: str
    status: CommandStatus
    error: str | None
    created_at: datetime
    completed_at: datetime | None


class GateCommandResult(BaseModel):
    success: bool
    error: str | None = PydanticField(default=None, max_length=300)


class GateDisplay(SQLModel, table=True):
    """Lo que ve el conductor en la pantalla del punto de ingreso o de salida."""

    __tablename__ = "gate_displays"
    __table_args__ = (UniqueConstraint("parking_lot_id", "gate", name="uq_display_lot_gate"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    parking_lot_id: UUID = Field(foreign_key="parking_lots.id", index=True)
    gate: Gate = Field(sa_type=EnumStr(Gate, 10))
    state: DisplayState = Field(default=DisplayState.IDLE, sa_type=EnumStr(DisplayState, 20))
    message: str = Field(default="", max_length=120)
    plate: str | None = Field(default=None, max_length=10)
    expires_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class GateDisplayIn(BaseModel):
    state: DisplayState
    message: str = PydanticField(max_length=120)
    plate: str | None = PydanticField(default=None, max_length=10)
    duration_seconds: float = PydanticField(default=6, gt=0, le=60)


class GateDisplayPublic(BaseModel):
    gate: Gate
    state: DisplayState
    message: str
    plate: str | None


def device_sort_key(device: Device) -> int:
    return list(DEVICE_CATALOG).index(device.code)
