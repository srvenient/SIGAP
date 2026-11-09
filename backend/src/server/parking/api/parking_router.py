from typing import Annotated

from fastapi import APIRouter, Depends

from src.server.audit.domain.audit_log import Actor
from src.server.auth.api.deps import AdminUserDep, CurrentUserDep
from src.server.parking.application.parking_service import ParkingService
from src.server.parking.domain.parking_lot import Occupancy, ParkingLotPublic, ParkingLotUpdate
from src.server.shared.api.deps import SessionDep
from src.server.wiring import build_parking_service


def _service(session: SessionDep) -> ParkingService:
    return build_parking_service(session)


ServiceDep = Annotated[ParkingService, Depends(_service)]

parking_router = APIRouter(prefix="/parking", tags=["Parking"])


@parking_router.get("", response_model=ParkingLotPublic)
async def get_parking(_: CurrentUserDep, service: ServiceDep):
    return await service.get()


@parking_router.patch("", response_model=ParkingLotPublic)
async def update_parking(body: ParkingLotUpdate, admin: AdminUserDep, service: ServiceDep):
    return await service.update(body, Actor.of(admin))


@parking_router.get("/occupancy", response_model=Occupancy)
async def get_occupancy(_: CurrentUserDep, service: ServiceDep):
    return await service.occupancy()
