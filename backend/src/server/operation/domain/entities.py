from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class ParkingLotBase(SQLModel):
    name: str = Field(max_length=100)

    address: str = Field(max_length=200)

    total_capacity: int = Field(default=0)
    available_capacity: int = Field(default=0)


class ParkingLot(ParkingLotBase, table=True):
    __tablename__ = "parkinglot"

    id: int | None = Field(default=None, primary_key=True)

    devices: list["Device"] = Relationship(back_populates="parking_lot")
    sessions: list["Session"] = Relationship(back_populates="parking_lot")


class DeviceType(Enum):
    ENTRY = "entry"
    EXIT = "exit"


class DeviceStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class DeviceBase(SQLModel):
    name: str = Field(max_length=100)
    type: DeviceType = Field(default=DeviceType.ENTRY)

    status: DeviceStatus = Field(default=DeviceStatus.DISCONNECTED)


class Device(DeviceBase, table=True):
    __tablename__ = "devices"

    id: int | None = Field(default=None, primary_key=True)

    parking_lot_id: int = Field(foreign_key="parkinglot.id")

    last_communication_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"name": "lastCommunicationAt"}
    )

    parking_lot: ParkingLot | None = Relationship(back_populates="devices")


class VehicleType(Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"


class SessionStatus(Enum):
    ENTERED = "entered"
    PAID = "paid"
    COMPLETED = "completed"


class SessionBase(SQLModel):
    status: SessionStatus = Field(default=SessionStatus.ENTERED)

    vehicle_type: VehicleType = Field(default=VehicleType.CAR)
    license_plate: str = Field(max_length=10, index=True)


class Session(SessionBase, table=True):
    __tablename__ = "transactions"

    id: int | None = Field(default=None, primary_key=True)

    parking_lot_id: int = Field(foreign_key="parkinglot.id")

    entry_device_id: int = Field(foreign_key="devices.id")
    exit_device_id: int = Field(foreign_key="devices.id")

    entry_timestamp: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"name": "entryTimestamp"})
    exit_timestamp: datetime | None = Field(default=None, sa_column_kwargs={"name": "exitTimestamp"})

    parking_lot: Optional[ParkingLot] = Relationship(back_populates="sessions")
