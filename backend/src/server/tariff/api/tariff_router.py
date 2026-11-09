from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.server.audit.domain.audit_log import Actor
from src.server.auth.api.deps import AdminUserDep
from src.server.shared.api.deps import SessionDep
from src.server.shared.application.date_range import day_bounds
from src.server.tariff.application.tariff_service import TariffService
from src.server.tariff.domain.tariff import (
    TariffHistoriesPublic,
    TariffHistoryPublic,
    TariffPublic,
    TariffUpdate,
)
from src.server.transaction.domain.plate import VehicleType
from src.server.wiring import build_tariff_service


def _service(session: SessionDep) -> TariffService:
    return build_tariff_service(session)


ServiceDep = Annotated[TariffService, Depends(_service)]

tariff_router = APIRouter(prefix="/tariffs", tags=["Tariffs"])


@tariff_router.get("", response_model=list[TariffPublic])
async def list_tariffs(_: AdminUserDep, service: ServiceDep):
    return await service.list_current()


@tariff_router.get("/history", response_model=TariffHistoriesPublic)
async def tariff_history(
        _: AdminUserDep,
        service: ServiceDep,
        vehicle_type: VehicleType | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
):
    start, end = day_bounds(date_from, date_to)
    rows, count = await service.history(vehicle_type, start, end, skip, limit)
    return TariffHistoriesPublic(data=[TariffHistoryPublic.model_validate(r) for r in rows], count=count)


@tariff_router.put("/{vehicle_type}", response_model=TariffPublic)
async def update_tariff(
        vehicle_type: VehicleType,
        body: TariffUpdate,
        admin: AdminUserDep,
        service: ServiceDep,
):
    return await service.update(vehicle_type, body, Actor.of(admin))
