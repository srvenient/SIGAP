from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends

from src.server.auth.api.deps import AdminUserDep
from src.server.reporting.application.reporting_service import ReportingService
from src.server.reporting.domain.report import Dashboard, Revenue
from src.server.shared.api.deps import SessionDep
from src.server.shared.application.date_range import day_bounds
from src.server.wiring import build_reporting_service


def _service(session: SessionDep) -> ReportingService:
    return build_reporting_service(session)


ServiceDep = Annotated[ReportingService, Depends(_service)]

reporting_router = APIRouter(prefix="/reports", tags=["Reports"])


@reporting_router.get("/dashboard", response_model=Dashboard)
async def dashboard(_: AdminUserDep, service: ServiceDep):
    return await service.dashboard()


@reporting_router.get("/revenue", response_model=Revenue)
async def revenue(
        _: AdminUserDep,
        service: ServiceDep,
        date_from: date | None = None,
        date_to: date | None = None,
):
    start, end = day_bounds(date_from, date_to)
    return await service.revenue(start, end)
