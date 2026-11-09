import asyncio
import base64
from datetime import timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from src.server.audit.domain.audit_log import AuditAction, AuditLog
from src.server.device.domain.device import Device, DeviceCode
from src.server.parking.domain.parking_lot import DEFAULT_PARKING_LOT_ID, ParkingLot
from src.server.payment.domain.payment_attempt import PaymentAttempt
from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.ticket.domain.ticket import Ticket
from src.server.transaction.domain.transaction import Transaction, TransactionStatus
from src.server.wiring import build_device_service, build_payment_service, build_transaction_service
from tests.conftest import DEVICE_HEADERS


async def enter(client: AsyncClient, plate: str = "ABC123", vehicle_type: str = "car", opened: bool = True) -> dict:
    response = await client.post(
        "/transactions/entry", json={"plate": plate, "vehicle_type": vehicle_type}, headers=DEVICE_HEADERS
    )
    assert response.status_code == 201, response.text
    data = response.json()
    if opened:
        gate = await client.post(f"/transactions/{data['id']}/entry-gate-opened", headers=DEVICE_HEADERS)
        assert gate.status_code == 200, gate.text
    return data


async def pay(client: AsyncClient, plate: str = "ABC123", outcome: str = "approved") -> dict:
    started = await client.post("/public/payments", json={"plate": plate, "method": "card"})
    assert started.status_code == 201, started.text
    reference = started.json()["reference"]
    result = await client.post(f"/public/payments/{reference}/simulate", json={"outcome": outcome})
    assert result.status_code == 200, result.text
    return result.json()


async def audit_actions(session: AsyncSession, label: str) -> list[AuditAction]:
    rows = await session.exec(select(AuditLog).where(AuditLog.entity_label == label))
    return [r.action for r in rows.all()]


async def age_transaction(session: AsyncSession, transaction_id: str, minutes: int) -> None:
    transaction = await session.get(Transaction, UUID(transaction_id))
    transaction.entry_time = get_localized_now() - timedelta(minutes=minutes)
    session.add(transaction)
    await session.commit()


# --- Ingreso (HU-02 a HU-05) ---

async def test_entry_requires_device_key(async_client: AsyncClient) -> None:
    response = await async_client.post("/transactions/entry", json={"plate": "ABC123", "vehicle_type": "car"})

    assert response.status_code == 401


async def test_entry_creates_transaction_with_system_values(async_client, db_session) -> None:
    data = await enter(async_client)

    assert data["status"] == "entered"
    assert data["plate"] == "ABC123"
    assert AuditAction.TRANSACTION_CREATED in await audit_actions(db_session, "ABC123")


async def test_entry_ignores_client_supplied_status_and_amount(async_client) -> None:
    response = await async_client.post(
        "/transactions/entry",
        json={"plate": "ABC123", "vehicle_type": "car", "status": "paid", "total_amount": 1},
        headers=DEVICE_HEADERS,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "entered"
    assert response.json()["total_amount"] is None


@pytest.mark.parametrize(
    ("plate", "vehicle_type"),
    [("ABC12D", "car"), ("ABC123", "motorcycle"), ("AB1234", "car"), ("ABCDEF", "car")],
)
async def test_entry_rejects_plate_that_does_not_match_type(async_client, plate: str, vehicle_type: str) -> None:
    response = await async_client.post(
        "/transactions/entry", json={"plate": plate, "vehicle_type": vehicle_type}, headers=DEVICE_HEADERS
    )

    assert response.status_code == 422


async def test_entry_rejects_vehicle_already_inside(async_client) -> None:
    await enter(async_client)

    response = await async_client.post(
        "/transactions/entry", json={"plate": "ABC-123", "vehicle_type": "car"}, headers=DEVICE_HEADERS
    )

    assert response.status_code == 400


async def test_entry_retry_returns_same_transaction_when_gate_never_opened(async_client) -> None:
    first = await enter(async_client, opened=False)

    response = await async_client.post(
        "/transactions/entry", json={"plate": "ABC123", "vehicle_type": "car"}, headers=DEVICE_HEADERS
    )

    assert response.status_code == 200
    assert response.json()["id"] == first["id"]


async def test_entry_rejected_when_parking_is_full(async_client, db_session) -> None:
    lot = await db_session.get(ParkingLot, DEFAULT_PARKING_LOT_ID)
    lot.capacity = 1
    db_session.add(lot)
    await db_session.commit()
    await enter(async_client)

    response = await async_client.post(
        "/transactions/entry", json={"plate": "XYZ987", "vehicle_type": "car"}, headers=DEVICE_HEADERS
    )

    assert response.status_code == 409


async def test_paid_vehicle_still_occupies_a_space(async_client, db_session, login) -> None:
    await enter(async_client)
    await pay(async_client)
    admin = await login("admin1")

    occupancy = (await admin.get("/parking/occupancy")).json()

    assert occupancy["occupied"] == 1


async def test_concurrent_entries_cannot_exceed_capacity(test_engine) -> None:
    """Sin savepoint: dos conexiones reales compiten por el último cupo."""
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        lot = await session.get(ParkingLot, DEFAULT_PARKING_LOT_ID)
        original = lot.capacity
        lot.capacity = 1
        session.add(lot)
        await session.commit()

    async def attempt(plate: str):
        async with AsyncSession(test_engine, expire_on_commit=False) as session:
            return await build_transaction_service(session).register_entry(plate, None)

    results = await asyncio.gather(attempt("RAC001"), attempt("RAC002"), return_exceptions=True)

    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        await session.exec(text("DELETE FROM transactions WHERE plate IN ('RAC001', 'RAC002')"))
        lot = await session.get(ParkingLot, DEFAULT_PARKING_LOT_ID)
        lot.capacity = original
        session.add(lot)
        await session.commit()

    assert len([r for r in results if not isinstance(r, Exception)]) == 1


# --- Pago (HU-07 a HU-09) ---

async def test_quote_applies_current_tariff(async_client, db_session) -> None:
    created = await enter(async_client)
    await age_transaction(db_session, created["id"], 61)

    quote = (await async_client.get("/public/quote/abc-123")).json()

    assert quote["minutes"] in (61, 62)
    assert quote["amount"] == 6000
    assert quote["status"] == "entered"


async def test_quote_applies_full_rate_and_new_period(async_client, db_session) -> None:
    created = await enter(async_client)
    await age_transaction(db_session, created["id"], 13 * 60)

    quote = (await async_client.get("/public/quote/ABC123")).json()

    assert quote["amount"] == 40000
    assert quote["periods"] == 2


async def test_quote_for_unknown_plate_returns_404(async_client) -> None:
    assert (await async_client.get("/public/quote/ZZZ999")).status_code == 404


async def test_pending_payment_keeps_transaction_entered(async_client, db_session) -> None:
    created = await enter(async_client)

    started = await async_client.post("/public/payments", json={"plate": "ABC123", "method": "pse"})

    assert started.json()["status"] == "pending"
    assert (await db_session.get(Transaction, UUID(created["id"]))).status == TransactionStatus.ENTERED


async def test_approved_payment_marks_paid_and_records_method(async_client, db_session) -> None:
    created = await enter(async_client)

    state = await pay(async_client)

    transaction = await db_session.get(Transaction, UUID(created["id"]))
    assert state["status"] == "approved"
    assert transaction.status == TransactionStatus.PAID
    assert transaction.payment_method == "card"
    assert transaction.paid_at is not None
    assert AuditAction.PAYMENT_APPROVED in await audit_actions(db_session, "ABC123")


async def test_rejected_payment_can_be_retried_and_is_audited(async_client, db_session) -> None:
    created = await enter(async_client)

    rejected = await pay(async_client, outcome="rejected")
    approved = await pay(async_client, outcome="approved")

    assert rejected["status"] == "rejected"
    assert approved["status"] == "approved"
    assert (await db_session.get(Transaction, UUID(created["id"]))).status == TransactionStatus.PAID

    failures = await db_session.exec(select(AuditLog).where(AuditLog.action == AuditAction.PAYMENT_FAILED))
    entry = failures.one()
    assert entry.entity_id == created["id"]
    assert {"medio", "referencia", "motivo"} <= set(entry.detail)


async def test_payment_timeout_expires_attempt_and_is_audited(async_client, db_session) -> None:
    await enter(async_client)
    started = (await async_client.post("/public/payments", json={"plate": "ABC123", "method": "card"})).json()
    attempt = (await db_session.exec(
        select(PaymentAttempt).where(PaymentAttempt.reference == started["reference"])
    )).one()
    attempt.created_at = get_localized_now() - timedelta(seconds=settings.PAYMENT_TIMEOUT_SECONDS + 1)
    db_session.add(attempt)
    await db_session.commit()

    assert await build_payment_service(db_session).expire_overdue() == 1

    state = (await async_client.get(f"/public/payments/{started['reference']}")).json()
    assert state["status"] == "expired"
    assert AuditAction.PAYMENT_FAILED in await audit_actions(db_session, "ABC123")


async def test_late_approval_after_timeout_does_not_mark_paid(async_client, db_session) -> None:
    created = await enter(async_client)
    started = (await async_client.post("/public/payments", json={"plate": "ABC123", "method": "card"})).json()
    attempt = (await db_session.exec(
        select(PaymentAttempt).where(PaymentAttempt.reference == started["reference"])
    )).one()
    attempt.created_at = get_localized_now() - timedelta(seconds=settings.PAYMENT_TIMEOUT_SECONDS + 1)
    db_session.add(attempt)
    await db_session.commit()

    result = await async_client.post(
        f"/public/payments/{started['reference']}/simulate", json={"outcome": "approved"}
    )

    assert result.json()["status"] == "expired"
    assert (await db_session.get(Transaction, UUID(created["id"]))).status == TransactionStatus.ENTERED


async def test_approval_is_idempotent(async_client, db_session) -> None:
    await enter(async_client)
    started = (await async_client.post("/public/payments", json={"plate": "ABC123", "method": "card"})).json()
    url = f"/public/payments/{started['reference']}/simulate"

    await async_client.post(url, json={"outcome": "approved"})
    second = await async_client.post(url, json={"outcome": "rejected"})

    assert second.json()["status"] == "approved"


async def test_invalid_payment_method_is_rejected(async_client) -> None:
    await enter(async_client)

    response = await async_client.post("/public/payments", json={"plate": "ABC123", "method": "bitcoin"})

    assert response.status_code == 422


# --- Salida (HU-11, HU-12) ---

async def test_exit_with_pending_payment_is_refused_and_alerts_operator(async_client, login) -> None:
    await enter(async_client)

    response = await async_client.post("/transactions/exit/ABC123/authorize", headers=DEVICE_HEADERS)

    assert response.status_code == 402
    operator = await login("oper1")
    alerts = (await operator.get("/interventions/alerts")).json()
    assert [a["alert_type"] for a in alerts] == ["payment_pending"]


async def test_exit_without_transaction_is_refused_and_alerts_operator(async_client, login) -> None:
    response = await async_client.post("/transactions/exit/ZZZ999/authorize", headers=DEVICE_HEADERS)

    assert response.status_code == 404
    operator = await login("oper1")
    alerts = (await operator.get("/interventions/alerts")).json()
    assert [a["alert_type"] for a in alerts] == ["no_active_transaction"]


async def test_repeated_exit_attempts_do_not_duplicate_alert(async_client, login) -> None:
    await async_client.post("/transactions/exit/ZZZ999/authorize", headers=DEVICE_HEADERS)
    await async_client.post("/transactions/exit/ZZZ999/authorize", headers=DEVICE_HEADERS)

    operator = await login("oper1")

    assert len((await operator.get("/interventions/alerts")).json()) == 1


async def test_authorize_does_not_change_state_until_gate_confirms(async_client, db_session) -> None:
    created = await enter(async_client)
    await pay(async_client)

    authorized = await async_client.post("/transactions/exit/ABC123/authorize", headers=DEVICE_HEADERS)

    assert authorized.status_code == 200
    transaction = await db_session.get(Transaction, UUID(created["id"]))
    assert transaction.status == TransactionStatus.PAID
    assert transaction.exit_time is None


async def test_confirm_exit_completes_transaction(async_client, db_session) -> None:
    created = await enter(async_client)
    await pay(async_client)

    confirmed = await async_client.post(f"/transactions/{created['id']}/exit-confirm", headers=DEVICE_HEADERS)

    assert confirmed.json()["status"] == "completed"
    assert confirmed.json()["exit_time"] is not None
    actions = await audit_actions(db_session, "ABC123")
    assert AuditAction.TRANSACTION_COMPLETED in actions
    assert AuditAction.GATE_OPENED in actions


async def test_confirm_exit_refused_when_not_paid(async_client) -> None:
    created = await enter(async_client)

    response = await async_client.post(f"/transactions/{created['id']}/exit-confirm", headers=DEVICE_HEADERS)

    assert response.status_code == 409


async def test_gate_failure_raises_ticket_and_keeps_transaction_paid(async_client, db_session) -> None:
    created = await enter(async_client)
    await pay(async_client)

    response = await async_client.post(
        "/devices/events",
        json={
            "device_code": "gate_exit",
            "error_code": "GATE_NO_RESPONSE",
            "description": "La talanquera no confirmó la apertura",
            "transaction_id": created["id"],
        },
        headers=DEVICE_HEADERS,
    )

    assert response.status_code == 204
    assert (await db_session.get(Transaction, UUID(created["id"]))).status == TransactionStatus.PAID
    ticket = (await db_session.exec(select(Ticket).where(Ticket.error_code == "GATE_NO_RESPONSE"))).one()
    assert ticket.status == "pending"
    assert ticket.assigned_role == "support"
    assert ticket.transaction_id == UUID(created["id"])
    assert ticket.technical_event_id is not None


async def test_repeated_failure_does_not_duplicate_open_ticket(async_client, db_session) -> None:
    payload = {"device_code": "gate_entry", "error_code": "GATE_NO_RESPONSE", "description": "Sin respuesta"}

    await async_client.post("/devices/events", json=payload, headers=DEVICE_HEADERS)
    await async_client.post("/devices/events", json=payload, headers=DEVICE_HEADERS)

    assert len((await db_session.exec(select(Ticket))).all()) == 1


# --- Tarifas (HU-13, HU-14) ---

TARIFF = {
    "hourly_rate": 5000,
    "fraction_rate": 2500,
    "fraction_minutes": 20,
    "full_rate": 30000,
    "full_rate_after_minutes": 240,
}


async def test_tariff_update_keeps_history_and_does_not_touch_settled(async_client, db_session, login) -> None:
    created = await enter(async_client)
    await pay(async_client)
    settled = float((await db_session.get(Transaction, UUID(created["id"]))).total_amount)
    admin = await login("admin1")

    updated = await admin.put("/tariffs/car", json=TARIFF)

    assert updated.status_code == 200
    assert updated.json()["hourly_rate"] == 5000
    transaction = await db_session.get(Transaction, UUID(created["id"]))
    assert float(transaction.total_amount) == settled
    assert transaction.tariff_snapshot["hourly_rate"] == 4000

    history = (await admin.get("/tariffs/history", params={"vehicle_type": "car"})).json()
    assert history["count"] == 1
    entry = history["data"][0]
    assert entry["previous_config"]["hourly_rate"] == 4000
    assert entry["new_config"]["hourly_rate"] == 5000
    assert entry["changed_by_username"] == "admin1"


async def test_new_tariff_applies_to_next_quote(async_client, db_session, login) -> None:
    created = await enter(async_client)
    await age_transaction(db_session, created["id"], 59)
    admin = await login("admin1")

    await admin.put("/tariffs/car", json=TARIFF)

    # 60 min: una hora exacta con la tarifa nueva
    assert (await async_client.get("/public/quote/ABC123")).json()["amount"] in (5000, 7500)


@pytest.mark.parametrize(
    "change",
    [{"hourly_rate": 0}, {"fraction_minutes": 0}, {"fraction_minutes": 60}, {"full_rate": -1},
     {"full_rate_after_minutes": 0}],
)
async def test_invalid_tariff_is_rejected(login, change: dict) -> None:
    admin = await login("admin1")

    response = await admin.put("/tariffs/car", json={**TARIFF, **change})

    assert response.status_code == 422


# --- Intervención manual (HU-06) ---

async def raise_unreadable(client: AsyncClient, gate: str = "entry") -> None:
    image = base64.b64encode(b"\xff\xd8\xff" + b"0" * 32).decode()
    response = await client.post(
        "/interventions/alerts",
        json={"gate": gate, "alert_type": "plate_unreadable", "message": "No se pudo leer", "snapshot_b64": image},
        headers=DEVICE_HEADERS,
    )
    assert response.status_code == 204, response.text


async def test_operator_resolves_unreadable_plate(async_client, db_session, login) -> None:
    await raise_unreadable(async_client)
    operator = await login("oper1")
    alert = (await operator.get("/interventions/alerts")).json()[0]
    assert alert["has_snapshot"] is True
    assert (await operator.get(f"/interventions/alerts/{alert['id']}/snapshot")).content.startswith(b"\xff\xd8\xff")

    response = await operator.post(
        f"/interventions/alerts/{alert['id']}/resolve", json={"plate": "DEF456", "reason": "Placa sucia"}
    )

    assert response.status_code == 202, response.text
    transaction = (await db_session.exec(select(Transaction).where(Transaction.plate == "DEF456"))).one()
    assert transaction.manual_intervention is True
    assert transaction.manual_reason == "Placa sucia"
    assert (await operator.get("/interventions/alerts")).json() == []
    assert AuditAction.ALERT_RESOLVED in await audit_actions(db_session, "DEF456")

    log = (await db_session.exec(select(AuditLog).where(AuditLog.action == AuditAction.ALERT_RESOLVED))).one()
    assert log.actor_label == "oper1"
    assert log.detail["motivo"] == "Placa sucia"


async def test_invalid_manual_plate_keeps_alert_pending(async_client, db_session, login) -> None:
    await raise_unreadable(async_client)
    operator = await login("oper1")
    alert = (await operator.get("/interventions/alerts")).json()[0]

    response = await operator.post(
        f"/interventions/alerts/{alert['id']}/resolve", json={"plate": "12345", "reason": "Intento"}
    )

    assert response.status_code == 422
    assert len((await operator.get("/interventions/alerts")).json()) == 1
    assert (await db_session.exec(select(Transaction))).all() == []


async def test_operator_corrects_plate_of_vehicle_inside(async_client, db_session, login) -> None:
    created = await enter(async_client)
    operator = await login("oper1")

    response = await operator.patch(
        f"/interventions/transactions/{created['id']}/plate",
        json={"plate": "ABC12D", "reason": "Era una moto"},
    )

    assert response.status_code == 200
    assert response.json()["plate"] == "ABC12D"
    assert response.json()["vehicle_type"] == "motorcycle"
    assert response.json()["manual_intervention"] is True


async def test_manual_open_flows_through_worker_and_is_audited(async_client, db_session, login) -> None:
    operator = await login("oper1")

    command = (await operator.post("/interventions/gates/exit/open", json={"reason": "Corte de energía"})).json()
    beat = await async_client.post(
        "/devices/heartbeat",
        json={"devices": [{"code": "gate_exit", "status": "connected"}]},
        headers=DEVICE_HEADERS,
    )
    assert [c["id"] for c in beat.json()["commands"]] == [command["id"]]

    done = await async_client.post(
        f"/devices/commands/{command['id']}/result", json={"success": True}, headers=DEVICE_HEADERS
    )

    assert done.status_code == 204
    log = (await db_session.exec(select(AuditLog).where(AuditLog.action == AuditAction.GATE_OPENED))).one()
    assert log.actor_label == "oper1"
    assert log.detail["modo"] == "manual"
    assert log.detail["motivo"] == "Corte de energía"


async def test_manual_exit_after_payment_completes_when_gate_opens(async_client, db_session, login) -> None:
    created = await enter(async_client)
    await pay(async_client)
    await raise_unreadable(async_client, gate="exit")
    operator = await login("oper1")
    alert = (await operator.get("/interventions/alerts")).json()[0]

    command = (await operator.post(
        f"/interventions/alerts/{alert['id']}/resolve", json={"plate": "ABC123", "reason": "Placa ilegible"}
    )).json()
    await async_client.post("/devices/heartbeat", json={"devices": []}, headers=DEVICE_HEADERS)
    await async_client.post(
        f"/devices/commands/{command['id']}/result", json={"success": True}, headers=DEVICE_HEADERS
    )

    transaction = await db_session.get(Transaction, UUID(created["id"]), populate_existing=True)
    assert transaction.status == TransactionStatus.COMPLETED
    assert transaction.manual_intervention is True


async def test_manual_exit_refused_when_unpaid(async_client, db_session, login) -> None:
    await enter(async_client)
    await raise_unreadable(async_client, gate="exit")
    operator = await login("oper1")
    alert = (await operator.get("/interventions/alerts")).json()[0]

    response = await operator.post(
        f"/interventions/alerts/{alert['id']}/resolve", json={"plate": "ABC123", "reason": "Placa ilegible"}
    )

    assert response.status_code == 402


# --- Dispositivos (HU-22, HU-24) ---

async def test_device_status_follows_heartbeat(async_client, login) -> None:
    support = await login("sup1")
    initial = {d["code"]: d["status"] for d in (await support.get("/devices")).json()}
    assert set(initial) == {"camera_entry", "camera_exit", "gate_entry", "gate_exit"}

    await async_client.post(
        "/devices/heartbeat",
        json={"devices": [
            {"code": "camera_entry", "status": "connected"},
            {"code": "gate_exit", "status": "error", "error": "Relé sin respuesta"},
        ]},
        headers=DEVICE_HEADERS,
    )

    devices = {d["code"]: d for d in (await support.get("/devices")).json()}
    assert devices["camera_entry"]["status"] == "connected"
    assert devices["camera_entry"]["last_seen_at"] is not None
    assert devices["gate_exit"]["status"] == "error"
    assert devices["gate_exit"]["last_error"] == "Relé sin respuesta"


async def test_device_error_opens_automatic_ticket(async_client, db_session) -> None:
    await async_client.post(
        "/devices/heartbeat",
        json={"devices": [{"code": "camera_exit", "status": "error", "error": "Sin imagen"}]},
        headers=DEVICE_HEADERS,
    )

    ticket = (await db_session.exec(select(Ticket).where(Ticket.error_code == "DEVICE_ERROR"))).one()
    assert ticket.origin == "automatic"
    assert ticket.component == "Cámara de salida"


async def test_silent_worker_is_detected_once(async_client, db_session, login) -> None:
    await async_client.post(
        "/devices/heartbeat",
        json={"devices": [{"code": "camera_entry", "status": "connected"}]},
        headers=DEVICE_HEADERS,
    )
    device = (await db_session.exec(select(Device).where(Device.code == DeviceCode.CAMERA_ENTRY))).one()
    device.last_report_at = get_localized_now() - timedelta(seconds=settings.DEVICE_OFFLINE_SECONDS + 5)
    db_session.add(device)
    await db_session.commit()

    service = build_device_service(db_session)
    assert await service.sweep_stale() == 1
    assert await service.sweep_stale() == 0

    support = await login("sup1")
    statuses = {d["code"]: d["status"] for d in (await support.get("/devices")).json()}
    assert statuses["camera_entry"] == "no_communication"
    tickets = (await db_session.exec(select(Ticket).where(Ticket.error_code == "WORKER_NO_COMMUNICATION"))).all()
    assert len(tickets) == 1


# --- Tickets (HU-23, HU-25) ---

async def test_ticket_lifecycle_preserves_history(login) -> None:
    operator = await login("oper1")
    support = await login("sup1")

    created = await operator.post("/tickets", json={"component": "Talanquera", "description": "No baja sola"})
    assert created.status_code == 201
    ticket_id = created.json()["id"]
    assert created.json()["status"] == "pending"
    assert created.json()["assigned_role"] == "support"

    taken = await support.post(f"/tickets/{ticket_id}/take")
    assert taken.json()["status"] == "in_review"
    assert taken.json()["assignee_username"] == "sup1"

    notes = await support.patch(f"/tickets/{ticket_id}/notes", json={"diagnosis": "Relé pegado"})
    assert notes.json()["diagnosis"] == "Relé pegado"

    closed = await support.post(
        f"/tickets/{ticket_id}/close",
        json={"status": "solved", "diagnosis": "Relé pegado", "actions_taken": "Se cambió", "result": "Funciona"},
    )
    assert closed.json()["status"] == "solved"

    detail = (await operator.get(f"/tickets/{ticket_id}")).json()
    assert [h["to_status"] for h in detail["history"]] == ["pending", "in_review", "solved"]
    assert detail["history"][1]["username"] == "sup1"


async def test_not_solved_ticket_can_be_taken_again(login) -> None:
    operator = await login("oper1")
    support = await login("sup1")
    ticket_id = (await operator.post("/tickets", json={"component": "Cámara", "description": "Imagen borrosa"})).json()["id"]
    await support.post(f"/tickets/{ticket_id}/take")
    await support.post(
        f"/tickets/{ticket_id}/close",
        json={"status": "not_solved", "diagnosis": "Lente", "actions_taken": "Limpieza", "result": "Persiste"},
    )

    retaken = await support.post(f"/tickets/{ticket_id}/take")

    assert retaken.json()["status"] == "in_review"


async def test_solved_ticket_cannot_be_reopened(login) -> None:
    operator = await login("oper1")
    support = await login("sup1")
    ticket_id = (await operator.post("/tickets", json={"component": "Cámara", "description": "Imagen borrosa"})).json()["id"]
    await support.post(f"/tickets/{ticket_id}/take")
    await support.post(
        f"/tickets/{ticket_id}/close",
        json={"status": "solved", "diagnosis": "Lente", "actions_taken": "Limpieza", "result": "Bien"},
    )

    assert (await support.post(f"/tickets/{ticket_id}/take")).status_code == 409


async def test_operator_only_sees_own_tickets(login) -> None:
    owner = await login("oper1")
    other = await login("oper2")
    ticket_id = (await owner.post("/tickets", json={"component": "Cámara", "description": "Imagen borrosa"})).json()["id"]

    assert (await other.get("/tickets")).json()["count"] == 0
    assert (await other.get(f"/tickets/{ticket_id}")).status_code == 404
    assert (await owner.get("/tickets")).json()["count"] == 1


# --- Consultas (HU-18 a HU-21) ---

async def test_inside_list_and_search(async_client, login) -> None:
    await enter(async_client, "ABC123")
    await enter(async_client, "XYZ98D", "motorcycle")
    operator = await login("oper1")

    assert len((await operator.get("/transactions/inside")).json()) == 2
    found = (await operator.get("/transactions/inside", params={"plate": "xyz"})).json()
    assert [t["plate"] for t in found] == ["XYZ98D"]


async def test_revenue_counts_only_collected_by_type_and_method(async_client, login) -> None:
    await enter(async_client, "ABC123")
    await enter(async_client, "XYZ98D", "motorcycle")
    await enter(async_client, "DEF456")
    await pay(async_client, "ABC123")
    await pay(async_client, "XYZ98D")
    admin = await login("admin1")

    revenue = (await admin.get("/reports/revenue")).json()

    assert revenue["count"] == 2
    assert revenue["total"] == 3000
    assert {r["key"] for r in revenue["by_vehicle_type"]} == {"car", "motorcycle"}
    assert revenue["by_payment_method"] == [{"key": "card", "total": 3000, "count": 2}]


async def test_dashboard_summarizes_the_day(async_client, login) -> None:
    created = await enter(async_client)
    await pay(async_client)
    await async_client.post(f"/transactions/{created['id']}/exit-confirm", headers=DEVICE_HEADERS)
    await enter(async_client, "DEF456")
    admin = await login("admin1")

    dashboard = (await admin.get("/reports/dashboard")).json()

    assert dashboard["entries_today"] == 2
    assert dashboard["exits_today"] == 1
    assert dashboard["revenue_today"] == 2000
    assert dashboard["occupancy"]["occupied"] == 1
    assert len(dashboard["devices"]) == 4


async def test_transaction_filters_and_detail(async_client, login) -> None:
    created = await enter(async_client, "ABC123")
    await enter(async_client, "XYZ98D", "motorcycle")
    await pay(async_client, "ABC123", "rejected")
    await pay(async_client, "ABC123", "approved")
    admin = await login("admin1")

    paid = (await admin.get("/transactions", params={"status": "paid"})).json()
    assert [t["plate"] for t in paid["data"]] == ["ABC123"]
    motos = (await admin.get("/transactions", params={"vehicle_type": "motorcycle"})).json()
    assert [t["plate"] for t in motos["data"]] == ["XYZ98D"]

    detail = (await admin.get(f"/transactions/{created['id']}")).json()
    assert detail["payment_method"] == "card"
    assert [a["status"] for a in detail["payment_attempts"]] == ["rejected", "approved"]


# --- Auditoría (HU-26 a HU-28) ---

async def test_login_and_logout_are_audited(async_client, db_session, login) -> None:
    client = await login("admin1")

    await client.post("/auth/logout")

    rows = (await db_session.exec(select(AuditLog).where(AuditLog.actor_label == "admin1"))).all()
    assert {AuditAction.LOGIN, AuditAction.LOGOUT} <= {r.action for r in rows}


async def test_failed_login_is_audited_without_revealing_cause(async_client, db_session) -> None:
    wrong_password = await async_client.post("/auth/login", data={"username": "admin1", "password": "Nope12345"})
    unknown_user = await async_client.post("/auth/login", data={"username": "nadie", "password": "Nope12345"})

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()
    rows = (await db_session.exec(select(AuditLog).where(AuditLog.action == AuditAction.LOGIN))).all()
    assert all(r.result == "failure" for r in rows)
    assert len(rows) == 2


async def test_queries_do_not_generate_audit_records(async_client, db_session, login) -> None:
    admin = await login("admin1")
    before = len((await db_session.exec(select(AuditLog))).all())

    await admin.get("/reports/dashboard")
    await admin.get("/transactions")
    await admin.get("/audit")

    assert len((await db_session.exec(select(AuditLog))).all()) == before


async def test_audit_filters(async_client, login) -> None:
    await enter(async_client)
    admin = await login("admin1")

    created = (await admin.get("/audit", params={"action": "transaction.created", "limit": 200})).json()
    entry = next(e for e in created["data"] if e["entity_label"] == "ABC123")
    assert entry["actor_label"] == "sistema"
    assert entry["result"] == "success"
    assert {e["action"] for e in created["data"]} == {"transaction.created"}
    logins = (await admin.get("/audit", params={"username": "admin1"})).json()
    assert logins["count"] >= 1
    assert {e["actor_label"] for e in logins["data"]} == {"admin1"}


async def test_audit_api_has_no_write_operations(async_client) -> None:
    paths = (await async_client.get("/openapi.json")).json()["paths"]

    assert set(paths["/api/v1/audit"]) == {"get"}
    assert set(paths["/api/v1/tariffs/history"]) == {"get"}


@pytest.mark.parametrize("statement", [
    "UPDATE audit_logs SET actor_label = 'alterado'",
    "DELETE FROM audit_logs",
    "TRUNCATE audit_logs",
])
async def test_database_rejects_changes_to_audit_logs(async_client, db_session, statement: str) -> None:
    await enter(async_client)

    with pytest.raises(DBAPIError, match="inmutables"):
        async with db_session.begin_nested():
            await db_session.exec(text(statement))


async def test_database_rejects_changes_to_tariff_history(db_session, login) -> None:
    admin = await login("admin1")
    await admin.put("/tariffs/car", json=TARIFF)

    with pytest.raises(DBAPIError, match="inmutables"):
        async with db_session.begin_nested():
            await db_session.exec(text("DELETE FROM tariff_history"))


async def test_database_rejects_changes_to_ticket_history(db_session, login) -> None:
    operator = await login("oper1")
    await operator.post("/tickets", json={"component": "Cámara", "description": "Imagen borrosa"})

    with pytest.raises(DBAPIError, match="inmutables"):
        async with db_session.begin_nested():
            await db_session.exec(text("UPDATE ticket_history SET note = 'x'"))


# --- Cuentas (HU-15 a HU-17) ---

@pytest.mark.parametrize("password", ["corta1A", "sinmayuscula1", "SINMINUSCULA1", "SinNumerooo"])
async def test_weak_password_is_rejected(login, password: str) -> None:
    admin = await login("admin1")
    roles = (await admin.get("/users/roles")).json()["roles"]

    response = await admin.post(
        "/users", json={"username": "nuevo", "password": password, "role_id": roles[0]["id"]}
    )

    assert response.status_code == 422


async def test_account_changes_are_audited(db_session, login) -> None:
    admin = await login("admin1")
    roles = (await admin.get("/users/roles")).json()["roles"]

    created = await admin.post(
        "/users", json={"username": "nuevo", "password": "Segura123", "role_id": roles[0]["id"]}
    )
    assert created.status_code == 201
    await admin.patch(f"/users/{created.json()['id']}", json={"is_active": False})

    actions = await audit_actions(db_session, "nuevo")
    assert AuditAction.USER_CREATED in actions
    assert AuditAction.USER_UPDATED in actions


async def test_inactive_account_gets_specific_message(async_client, db_session, login) -> None:
    admin = await login("admin1")
    roles = (await admin.get("/users/roles")).json()["roles"]
    created = await admin.post(
        "/users", json={"username": "baja", "password": "Segura123", "role_id": roles[0]["id"]}
    )
    await admin.patch(f"/users/{created.json()['id']}", json={"is_active": False})

    response = await async_client.post("/auth/login", data={"username": "baja", "password": "Segura123"})

    assert response.status_code == 403


# --- Matriz de permisos ---

@pytest.mark.parametrize(
    ("username", "method", "path", "allowed"),
    [
        ("oper1", "get", "/users", False),
        ("sup1", "get", "/users", False),
        ("admin1", "get", "/users", True),
        ("oper1", "get", "/tariffs", False),
        ("sup1", "get", "/tariffs", False),
        ("admin1", "get", "/tariffs", True),
        ("oper1", "get", "/audit", False),
        ("sup1", "get", "/audit", False),
        ("admin1", "get", "/audit", True),
        ("oper1", "get", "/reports/revenue", False),
        ("sup1", "get", "/reports/dashboard", False),
        ("admin1", "get", "/reports/dashboard", True),
        ("oper1", "get", "/transactions", False),
        ("admin1", "get", "/transactions", True),
        ("sup1", "get", "/transactions/inside", False),
        ("oper1", "get", "/transactions/inside", True),
        ("admin1", "get", "/transactions/inside", True),
        ("sup1", "get", "/interventions/alerts", False),
        ("oper1", "get", "/interventions/alerts", True),
        ("oper1", "get", "/devices", False),
        ("sup1", "get", "/devices", True),
        ("admin1", "get", "/devices", True),
        ("admin1", "get", "/tickets", False),
        ("oper1", "get", "/tickets", True),
        ("sup1", "get", "/tickets", True),
    ],
)
async def test_permission_matrix(login, username: str, method: str, path: str, allowed: bool) -> None:
    client = await login(username)

    response = await getattr(client, method)(path)

    assert (response.status_code == 200) is allowed, f"{username} {path}: {response.status_code}"


async def test_only_support_manages_tickets(login) -> None:
    operator = await login("oper1")
    ticket_id = (await operator.post("/tickets", json={"component": "Cámara", "description": "Imagen borrosa"})).json()["id"]

    assert (await operator.post(f"/tickets/{ticket_id}/take")).status_code == 403


async def test_support_cannot_create_tickets(login) -> None:
    support = await login("sup1")

    response = await support.post("/tickets", json={"component": "Cámara", "description": "Imagen borrosa"})

    assert response.status_code == 403
