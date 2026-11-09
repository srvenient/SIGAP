from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from src.server.audit.domain.audit_log import Actor
from src.server.auth.api.deps import OperatorOrAdminDep
from src.server.device.api.deps import DeviceServiceDep
from src.server.device.domain.device import Gate, GateCommandPublic
from src.server.intervention.api.deps import InterventionServiceDep
from src.server.intervention.domain.alert import AlertIn, AlertPublic, AlertStatus, ManualPlate, Reason
from src.server.shared.api.deps import DeviceKeyDep
from src.server.transaction.api.deps import TransactionServiceDep
from src.server.transaction.domain.transaction import TransactionPublic

intervention_router = APIRouter(prefix="/interventions", tags=["Interventions"])


@intervention_router.post("/alerts", status_code=status.HTTP_204_NO_CONTENT)
async def raise_alert(_: DeviceKeyDep, body: AlertIn, service: InterventionServiceDep):
    await service.raise_from_device(body)


@intervention_router.get("/alerts", response_model=list[AlertPublic])
async def list_alerts(
        _: OperatorOrAdminDep,
        service: InterventionServiceDep,
        alert_status: AlertStatus | None = Query(default=AlertStatus.PENDING, alias="status"),
        limit: int = Query(50, ge=1, le=200),
):
    return await service.search(alert_status, limit)


@intervention_router.get("/alerts/{alert_id}/snapshot")
async def alert_snapshot(alert_id: UUID, _: OperatorOrAdminDep, service: InterventionServiceDep):
    return Response(
        content=await service.snapshot(alert_id),
        media_type="image/jpeg",
        headers={"Cache-Control": "private, no-store"},
    )


@intervention_router.post(
    "/alerts/{alert_id}/resolve", response_model=GateCommandPublic, status_code=status.HTTP_202_ACCEPTED
)
async def resolve_alert(
        alert_id: UUID, body: ManualPlate, user: OperatorOrAdminDep, service: InterventionServiceDep
):
    return await service.resolve(alert_id, body.plate, body.reason, Actor.of(user))


@intervention_router.post("/alerts/{alert_id}/dismiss", response_model=AlertPublic)
async def dismiss_alert(
        alert_id: UUID, body: Reason, user: OperatorOrAdminDep, service: InterventionServiceDep
):
    return await service.dismiss(alert_id, body.reason, Actor.of(user))


@intervention_router.post(
    "/manual-entry", response_model=GateCommandPublic, status_code=status.HTTP_202_ACCEPTED
)
async def manual_entry(body: ManualPlate, user: OperatorOrAdminDep, service: InterventionServiceDep):
    return await service.manual_entry(body.plate, body.reason, Actor.of(user))


@intervention_router.patch("/transactions/{transaction_id}/plate", response_model=TransactionPublic)
async def correct_plate(
        transaction_id: UUID, body: ManualPlate, user: OperatorOrAdminDep, service: TransactionServiceDep
):
    return await service.correct_plate(transaction_id, body.plate, body.reason, Actor.of(user))


@intervention_router.post(
    "/gates/{gate}/open", response_model=GateCommandPublic, status_code=status.HTTP_202_ACCEPTED
)
async def open_gate(gate: Gate, body: Reason, user: OperatorOrAdminDep, service: InterventionServiceDep):
    return await service.open_gate(gate, body.reason, Actor.of(user))


@intervention_router.get("/commands", response_model=list[GateCommandPublic])
async def recent_commands(_: OperatorOrAdminDep, service: DeviceServiceDep):
    return await service.recent_commands()
