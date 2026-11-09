from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query, Response, status
from pydantic import BaseModel

from src.server.auth.api.deps import AdminUserDep, OperatorOrAdminDep
from src.server.intervention.api.deps import InterventionServiceDep
from src.server.intervention.domain.alert import AlertType
from src.server.payment.api.deps import PaymentServiceDep
from src.server.payment.domain.payment_attempt import PaymentAttemptPublic
from src.server.shared.api.deps import DeviceKeyDep
from src.server.shared.application.date_range import day_bounds
from src.server.transaction.api.deps import TransactionServiceDep
from src.server.transaction.domain.plate import VehicleType, normalize_plate
from src.server.transaction.domain.transaction import (
    NoActiveTransaction,
    PaymentPending,
    TransactionCreate,
    TransactionPublic,
    TransactionsPublic,
    TransactionStatus,
)
from src.server.transaction.domain.transaction_repository import TransactionFilters

transaction_router = APIRouter(prefix="/transactions", tags=["Transactions"])


class TransactionDetail(TransactionPublic):
    tariff_snapshot: dict | None = None
    payment_attempts: list[PaymentAttemptPublic] = []


# --- Worker de cámaras (X-Device-Key) ---

@transaction_router.post("/entry", response_model=TransactionPublic, status_code=status.HTTP_201_CREATED)
async def create_entry(
        _: DeviceKeyDep,
        data: TransactionCreate,
        response: Response,
        service: TransactionServiceDep,
):
    transaction, created = await service.register_entry(data.plate, data.vehicle_type)
    if not created:
        response.status_code = status.HTTP_200_OK
    return transaction


@transaction_router.post("/{transaction_id}/entry-gate-opened", response_model=TransactionPublic)
async def entry_gate_opened(_: DeviceKeyDep, transaction_id: UUID, service: TransactionServiceDep):
    return await service.mark_entry_gate_opened(transaction_id)


@transaction_router.post("/exit/{plate}/authorize", response_model=TransactionPublic)
async def authorize_exit(
        _: DeviceKeyDep,
        plate: str,
        service: TransactionServiceDep,
        interventions: InterventionServiceDep,
):
    try:
        return await service.authorize_exit(plate)
    except PaymentPending:
        await interventions.raise_exit_alert(AlertType.PAYMENT_PENDING, normalize_plate(plate))
        raise
    except NoActiveTransaction:
        await interventions.raise_exit_alert(AlertType.NO_ACTIVE_TRANSACTION, normalize_plate(plate))
        raise


@transaction_router.post("/{transaction_id}/exit-confirm", response_model=TransactionPublic)
async def confirm_exit(_: DeviceKeyDep, transaction_id: UUID, service: TransactionServiceDep):
    return await service.confirm_exit(transaction_id)


# --- Consulta ---

@transaction_router.get("/inside", response_model=list[TransactionPublic])
async def vehicles_inside(
        _: OperatorOrAdminDep,
        service: TransactionServiceDep,
        plate: str | None = Query(default=None, max_length=10),
):
    return await service.list_inside(plate)


@transaction_router.get("", response_model=TransactionsPublic)
async def list_transactions(
        _: AdminUserDep,
        service: TransactionServiceDep,
        plate: str | None = Query(default=None, max_length=10),
        vehicle_type: VehicleType | None = None,
        transaction_status: TransactionStatus | None = Query(default=None, alias="status"),
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
):
    start, end = day_bounds(date_from, date_to)
    filters = TransactionFilters(
        plate=normalize_plate(plate) if plate else None,
        vehicle_type=vehicle_type,
        status=transaction_status,
        start=start,
        end=end,
    )
    rows, count = await service.search(filters, skip, limit)
    return TransactionsPublic(data=[TransactionPublic.model_validate(r) for r in rows], count=count)


@transaction_router.get("/{transaction_id}", response_model=TransactionDetail)
async def transaction_detail(
        _: AdminUserDep,
        transaction_id: UUID,
        service: TransactionServiceDep,
        payments: PaymentServiceDep,
):
    transaction = await service.get(transaction_id)
    attempts = await payments.attempts_of(transaction_id)
    return TransactionDetail(
        **TransactionPublic.model_validate(transaction).model_dump(),
        tariff_snapshot=transaction.tariff_snapshot,
        payment_attempts=[PaymentAttemptPublic.model_validate(a) for a in attempts],
    )
