from pydantic import BaseModel

from src.server.device.domain.device import DevicePublic
from src.server.parking.domain.parking_lot import Occupancy


class RevenueLine(BaseModel):
    key: str
    total: float
    count: int


class Revenue(BaseModel):
    total: float
    count: int
    by_vehicle_type: list[RevenueLine]
    by_payment_method: list[RevenueLine]


class Dashboard(BaseModel):
    occupancy: Occupancy
    revenue_today: float
    entries_today: int
    exits_today: int
    devices: list[DevicePublic]
