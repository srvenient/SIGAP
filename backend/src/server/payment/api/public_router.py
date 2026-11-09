from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from core.config import settings
from core.rate_limit import limiter
from src.server.audit.domain.audit_log import DRIVER
from src.server.device.api.deps import DeviceServiceDep
from src.server.device.domain.device import Gate, GateDisplayPublic
from src.server.parking.domain.parking_lot import Occupancy
from src.server.payment.api.deps import PaymentServiceDep
from src.server.payment.domain.payment_attempt import PaymentMethods, PaymentStart, PaymentState, Quote

# Interfaz operativa: el conductor no tiene cuenta. Solo expone placa, tipo, tiempo y valor.
public_router = APIRouter(prefix="/public", tags=["Public"])


class GateDisplayResponse(BaseModel):
    display: GateDisplayPublic
    occupancy: Occupancy


class SimulatedOutcome(BaseModel):
    outcome: Literal["approved", "rejected"]


@public_router.get("/quote/{plate}", response_model=Quote)
@limiter.limit(settings.PUBLIC_QUOTE_RATE_LIMIT)
async def quote(request: Request, plate: str, service: PaymentServiceDep):
    return await service.quote(plate)


@public_router.get("/payment-methods", response_model=PaymentMethods)
async def payment_methods(service: PaymentServiceDep):
    return service.methods()


@public_router.post("/payments", response_model=PaymentState, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.PUBLIC_QUOTE_RATE_LIMIT)
async def start_payment(request: Request, body: PaymentStart, service: PaymentServiceDep):
    return await service.start(body.plate, body.method)


@public_router.get("/payments/{reference}", response_model=PaymentState)
@limiter.limit(settings.PUBLIC_RATE_LIMIT)
async def payment_state(request: Request, reference: str, service: PaymentServiceDep):
    return await service.state(reference)


@public_router.post("/payments/{reference}/cancel", response_model=PaymentState)
@limiter.limit(settings.PUBLIC_RATE_LIMIT)
async def cancel_payment(request: Request, reference: str, service: PaymentServiceDep):
    return await service.cancel(reference)


@public_router.post("/payments/{reference}/simulate", response_model=PaymentState)
@limiter.limit(settings.PUBLIC_RATE_LIMIT)
async def simulate_payment(
        request: Request, reference: str, body: SimulatedOutcome, service: PaymentServiceDep
):
    # Solo existe con la pasarela simulada; con una real, el resultado llega por webhook firmado.
    if not service.gateway.simulated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not Found")
    return await service.apply_result(reference, body.outcome == "approved", actor=DRIVER)


@public_router.get("/gates/{gate}/display", response_model=GateDisplayResponse)
@limiter.limit(settings.PUBLIC_RATE_LIMIT)
async def gate_display(request: Request, gate: Gate, service: DeviceServiceDep):
    display, occupancy = await service.public_display(gate)
    return GateDisplayResponse(display=display, occupancy=occupancy)
