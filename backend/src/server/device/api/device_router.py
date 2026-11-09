from uuid import UUID

from fastapi import APIRouter, Query, status
from sqlmodel import SQLModel

from src.server.auth.api.deps import SupportOrAdminDep
from src.server.device.api.deps import DeviceServiceDep
from src.server.device.domain.device import (
    DevicePublic,
    Gate,
    GateCommandResult,
    GateDisplayIn,
    Heartbeat,
    HeartbeatResponse,
    TechnicalEventIn,
    TechnicalEventPublic,
)
from src.server.shared.api.deps import DeviceKeyDep

device_router = APIRouter(prefix="/devices", tags=["Devices"])


class TechnicalEventsPublic(SQLModel):
    data: list[TechnicalEventPublic]
    count: int


# --- Worker de cámaras (X-Device-Key) ---

@device_router.post("/heartbeat", response_model=HeartbeatResponse)
async def heartbeat(_: DeviceKeyDep, body: Heartbeat, service: DeviceServiceDep):
    return await service.heartbeat(body.devices)


@device_router.post("/events", status_code=status.HTTP_204_NO_CONTENT)
async def report_event(_: DeviceKeyDep, body: TechnicalEventIn, service: DeviceServiceDep):
    await service.report_event(body)


@device_router.post("/commands/{command_id}/result", status_code=status.HTTP_204_NO_CONTENT)
async def command_result(
        _: DeviceKeyDep, command_id: UUID, body: GateCommandResult, service: DeviceServiceDep
):
    await service.complete_command(command_id, body.success, body.error)


@device_router.put("/display/{gate}", status_code=status.HTTP_204_NO_CONTENT)
async def set_display(_: DeviceKeyDep, gate: Gate, body: GateDisplayIn, service: DeviceServiceDep):
    await service.set_display(gate, body)


# --- Consulta ---

@device_router.get("", response_model=list[DevicePublic])
async def list_devices(_: SupportOrAdminDep, service: DeviceServiceDep):
    return await service.list_public()


@device_router.get("/events", response_model=TechnicalEventsPublic)
async def list_events(
        _: SupportOrAdminDep,
        service: DeviceServiceDep,
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
):
    rows, count = await service.events(skip, limit)
    return TechnicalEventsPublic(data=[TechnicalEventPublic.model_validate(r) for r in rows], count=count)
