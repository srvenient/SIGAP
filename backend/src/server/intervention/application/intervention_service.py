import base64
import binascii
from uuid import UUID

from src.server.audit.application.audit_recorder import AuditRecorder
from src.server.audit.domain.audit_log import Actor, AuditAction
from src.server.device.application.device_service import DeviceService
from src.server.device.domain.device import Gate, GateCommand
from src.server.intervention.domain.alert import (
    AlertAlreadyClosed,
    AlertIn,
    AlertNotFound,
    AlertSnapshot,
    AlertStatus,
    AlertType,
    OperationAlert,
)
from src.server.intervention.domain.alert_repository import AlertRepository
from src.server.parking.domain.parking_lot_repository import ParkingLotRepository
from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.transaction.application.transaction_service import TransactionService
from src.server.transaction.domain.transaction import Transaction

MAX_SNAPSHOT_BYTES = 256 * 1024
JPEG_MAGIC = b"\xff\xd8\xff"

_EXIT_MESSAGES = {
    AlertType.PAYMENT_PENDING: "Vehículo en la salida con el pago pendiente",
    AlertType.NO_ACTIVE_TRANSACTION: "Vehículo en la salida sin transacción activa",
}


def _decode_snapshot(data: str | None) -> bytes | None:
    """Descarta lo que no sea un JPEG razonable en vez de guardar datos arbitrarios."""
    if not data:
        return None
    try:
        image = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        return None
    if len(image) > MAX_SNAPSHOT_BYTES or not image.startswith(JPEG_MAGIC):
        return None
    return image


class InterventionService:
    def __init__(
            self,
            repository: AlertRepository,
            parking_lots: ParkingLotRepository,
            transactions: TransactionService,
            devices: DeviceService,
            audit: AuditRecorder,
    ):
        self.repository = repository
        self.parking_lots = parking_lots
        self.transactions = transactions
        self.devices = devices
        self.audit = audit

    async def _create(
            self, gate: Gate, alert_type: AlertType, message: str, plate: str | None, snapshot: bytes | None = None
    ) -> OperationAlert:
        duplicate = await self.repository.find_pending_duplicate(alert_type, gate, plate)
        if duplicate is not None and alert_type != AlertType.PLATE_UNREADABLE:
            return duplicate

        lot = await self.parking_lots.get_default()
        alert = OperationAlert(
            parking_lot_id=lot.id,
            gate=gate,
            alert_type=alert_type,
            plate_read=plate,
            message=message,
            has_snapshot=snapshot is not None,
        )
        self.repository.add(alert)
        if snapshot is not None:
            await self.repository.flush()
            self.repository.add(AlertSnapshot(alert_id=alert.id, image=snapshot))
        await self.repository.commit()
        return alert

    async def raise_exit_alert(self, alert_type: AlertType, plate: str) -> OperationAlert:
        return await self._create(Gate.EXIT, alert_type, _EXIT_MESSAGES[alert_type], plate)

    async def raise_from_device(self, data: AlertIn) -> OperationAlert:
        return await self._create(
            data.gate, data.alert_type, data.message, data.plate_read, _decode_snapshot(data.snapshot_b64)
        )

    async def search(self, status: AlertStatus | None, limit: int) -> list[OperationAlert]:
        return await self.repository.search(status, limit)

    async def snapshot(self, alert_id: UUID) -> bytes:
        stored = await self.repository.get_snapshot(alert_id)
        if stored is None:
            raise AlertNotFound
        return stored.image

    async def _pending(self, alert_id: UUID) -> OperationAlert:
        alert = await self.repository.find_by_id(alert_id, for_update=True)
        if alert is None:
            raise AlertNotFound
        if alert.status != AlertStatus.PENDING:
            raise AlertAlreadyClosed
        return alert

    async def _close(self, alert: OperationAlert, status: AlertStatus, reason: str, actor: Actor) -> None:
        alert.status = status
        alert.resolution_note = reason
        alert.resolved_by_id = actor.user_id
        alert.resolved_by_username = actor.label
        alert.resolved_at = get_localized_now()
        alert.has_snapshot = False
        await self.repository.delete_snapshot(alert.id)
        self.repository.add(alert)

    async def resolve(self, alert_id: UUID, plate: str, reason: str, actor: Actor) -> GateCommand:
        """Registra la placa correcta y continúa el flujo normal (HU-06).

        El cierre de la alerta se confirma en el mismo commit que la transacción, de modo que si
        la placa es inválida, o la salida no está pagada, la alerta sigue pendiente.
        """
        alert = await self._pending(alert_id)
        await self._close(alert, AlertStatus.RESOLVED, reason, actor)
        self.audit.record(
            AuditAction.ALERT_RESOLVED, actor, "alert", alert.id, plate,
            detail={"placa_leida": alert.plate_read, "placa": plate, "motivo": reason},
        )

        if alert.gate == Gate.ENTRY:
            transaction, _ = await self.transactions.register_entry(plate, None, actor, manual_reason=reason)
        else:
            transaction = await self._authorize_manual_exit(plate, reason)

        alert.transaction_id = transaction.id
        self.repository.add(alert)
        return await self.devices.enqueue_open(alert.gate, actor, reason, transaction.id)

    async def _authorize_manual_exit(self, plate: str, reason: str) -> Transaction:
        transaction = await self.transactions.authorize_exit(plate)
        return await self.transactions.flag_manual_intervention(transaction, reason)

    async def dismiss(self, alert_id: UUID, reason: str, actor: Actor) -> OperationAlert:
        alert = await self._pending(alert_id)
        await self._close(alert, AlertStatus.DISMISSED, reason, actor)
        self.audit.record(
            AuditAction.ALERT_DISMISSED, actor, "alert", alert.id, alert.plate_read, detail={"motivo": reason}
        )
        await self.repository.commit()
        return alert

    async def manual_entry(self, plate: str, reason: str, actor: Actor) -> GateCommand:
        transaction, _ = await self.transactions.register_entry(plate, None, actor, manual_reason=reason)
        return await self.devices.enqueue_open(Gate.ENTRY, actor, reason, transaction.id)

    async def open_gate(self, gate: Gate, reason: str, actor: Actor) -> GateCommand:
        """Apertura por contingencia: no cambia el estado de ninguna transacción."""
        return await self.devices.enqueue_open(gate, actor, reason)
