from datetime import datetime

from src.server.device.application.device_service import DeviceService
from src.server.parking.application.parking_service import ParkingService
from src.server.reporting.domain.report import Dashboard, Revenue
from src.server.reporting.domain.report_repository import ReportRepository
from src.server.shared.application.date_range import today_bounds


class ReportingService:
    def __init__(self, repository: ReportRepository, parking: ParkingService, devices: DeviceService):
        self.repository = repository
        self.parking = parking
        self.devices = devices

    async def revenue(self, start: datetime | None, end: datetime | None) -> Revenue:
        return await self.repository.revenue(start, end)

    async def dashboard(self) -> Dashboard:
        start, end = today_bounds()
        revenue = await self.repository.revenue(start, end)
        return Dashboard(
            occupancy=await self.parking.occupancy(),
            revenue_today=revenue.total,
            entries_today=await self.repository.count_entries(start, end),
            exits_today=await self.repository.count_exits(start, end),
            devices=await self.devices.list_public(),
        )
