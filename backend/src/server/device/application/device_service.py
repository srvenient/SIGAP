from datetime import datetime, timedelta
from uuid import UUID

from core.config import settings
from src.server.audit.application.audit_recorder import AuditRecorder
from src.server.audit.domain.audit_log import SYSTEM, Actor, AuditAction, AuditResult
from src.server.device.domain.device import (
    GATE_DEVICE,
    CommandNotFound,
    CommandStatus,
    Device,
    DevicePublic,
    DeviceReport,
    DeviceStatus,
    DisplayState,
    Gate,
    GateCommand,
    GateCommandOut,
    GateDisplay,
    GateDisplayIn,
    GateDisplayPublic,
    HeartbeatResponse,
    TechnicalEvent,
    TechnicalEventIn,
    device_sort_key,
)
from src.server.device.domain.device_repository import DeviceRepository
from src.server.parking.domain.parking_lot import Occupancy
from src.server.parking.domain.parking_lot_repository import ParkingLotRepository
from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.ticket.application.ticket_service import TicketService
from src.server.transaction.application.transaction_service import TransactionService
from src.server.transaction.domain.transaction_repository import TransactionRepository

_ERROR_CODES = {
    DeviceStatus.ERROR: "DEVICE_ERROR",
    DeviceStatus.NO_COMMUNICATION: "DEVICE_NO_COMMUNICATION",
}
WORKER_COMPONENT = "Worker de cámaras"


def effective_status(device: Device, now: datetime) -> DeviceStatus:
    """Si el worker dejó de reportar, lo último que dijo ya no es confiable."""
    if device.last_report_at is None:
        return DeviceStatus.NO_COMMUNICATION
    if (now - device.last_report_at).total_seconds() > settings.DEVICE_OFFLINE_SECONDS:
        return DeviceStatus.NO_COMMUNICATION
    return device.reported_status


class DeviceService:
    def __init__(
            self,
            repository: DeviceRepository,
            parking_lots: ParkingLotRepository,
            transactions: TransactionRepository,
            transaction_service: TransactionService,
            tickets: TicketService,
            audit: AuditRecorder,
    ):
        self.repository = repository
        self.parking_lots = parking_lots
        self.transactions = transactions
        self.transaction_service = transaction_service
        self.tickets = tickets
        self.audit = audit

    async def list_public(self) -> list[DevicePublic]:
        lot = await self.parking_lots.get_default()
        now = get_localized_now()
        devices = sorted(await self.repository.list_devices(lot.id), key=device_sort_key)
        return [
            DevicePublic(
                code=d.code,
                kind=d.kind,
                name=d.name,
                status=effective_status(d, now),
                last_error=d.last_error,
                last_seen_at=d.last_seen_at,
            )
            for d in devices
        ]

    async def events(self, skip: int, limit: int) -> tuple[list[TechnicalEvent], int]:
        return await self.repository.list_events(skip, limit)

    async def heartbeat(self, reports: list[DeviceReport]) -> HeartbeatResponse:
        lot = await self.parking_lots.get_default()
        now = get_localized_now()
        by_code = {d.code: d for d in await self.repository.lock_devices(lot.id)}

        for report in reports:
            device = by_code.get(report.code)
            if device is None:
                continue

            changed = device.reported_status != report.status
            device.reported_status = report.status
            device.last_report_at = now
            device.last_error = report.error if report.status != DeviceStatus.CONNECTED else None
            if report.status == DeviceStatus.CONNECTED:
                device.last_seen_at = now
            self.repository.add(device)

            if changed and report.status != DeviceStatus.CONNECTED:
                await self._raise_event(
                    lot.id, device, device.name, _ERROR_CODES[report.status],
                    report.error or f"{device.name}: {report.status.value}",
                )

        commands = await self._collect_commands(lot.id, now)
        await self.repository.commit()
        return HeartbeatResponse(gate_open_seconds=lot.gate_open_seconds, commands=commands)

    async def _collect_commands(self, parking_lot_id: UUID, now: datetime) -> list[GateCommandOut]:
        ttl = timedelta(seconds=settings.GATE_COMMAND_TTL_SECONDS)
        to_send: list[GateCommandOut] = []
        for command in await self.repository.lock_open_commands(parking_lot_id):
            if now - command.created_at > ttl:
                command.status = CommandStatus.EXPIRED
                command.completed_at = now
                self.audit.record(
                    AuditAction.GATE_OPEN_FAILED, SYSTEM, "gate", command.gate.value, command.gate.value,
                    result=AuditResult.FAILURE, detail={"motivo": "La orden no se ejecutó a tiempo"},
                )
            elif command.status == CommandStatus.PENDING:
                command.status = CommandStatus.SENT
                to_send.append(GateCommandOut(id=command.id, gate=command.gate))
            self.repository.add(command)
        return to_send

    async def report_event(self, data: TechnicalEventIn) -> TechnicalEvent:
        lot = await self.parking_lots.get_default()
        device = next(
            (d for d in await self.repository.list_devices(lot.id) if d.code == data.device_code), None
        )
        event = await self._raise_event(
            lot.id, device, device.name if device else data.device_code.value,
            data.error_code, data.description, data.transaction_id,
        )
        await self.repository.commit()
        return event

    async def _raise_event(
            self,
            parking_lot_id: UUID,
            device: Device | None,
            component: str,
            error_code: str,
            description: str,
            transaction_id: UUID | None = None,
    ) -> TechnicalEvent:
        event = TechnicalEvent(
            parking_lot_id=parking_lot_id,
            device_id=device.id if device else None,
            component=component,
            error_code=error_code,
            description=description[:500],
            transaction_id=transaction_id,
        )
        self.repository.add(event)
        await self.repository.flush()
        await self.tickets.open_automatic(event)
        return event

    async def sweep_stale(self) -> int:
        """Detecta que el worker dejó de reportar. Un solo ticket por todos sus dispositivos."""
        cutoff = get_localized_now() - timedelta(seconds=settings.DEVICE_OFFLINE_SECONDS)
        stale = await self.repository.lock_stale(cutoff)
        for device in stale:
            device.reported_status = DeviceStatus.NO_COMMUNICATION
            self.repository.add(device)
        if stale:
            await self._raise_event(
                stale[0].parking_lot_id, None, WORKER_COMPONENT, "WORKER_NO_COMMUNICATION",
                "El worker de cámaras dejó de reportar el estado de los dispositivos.",
            )
        await self.repository.commit()
        return len(stale)

    async def enqueue_open(
            self, gate: Gate, actor: Actor, reason: str, transaction_id: UUID | None = None
    ) -> GateCommand:
        lot = await self.parking_lots.get_default()
        command = GateCommand(
            parking_lot_id=lot.id,
            gate=gate,
            transaction_id=transaction_id,
            reason=reason,
            requested_by_id=actor.user_id,
            requested_by_username=actor.label,
        )
        self.repository.add(command)
        self.audit.record(
            AuditAction.GATE_OPEN_REQUESTED, actor, "gate", gate.value, gate.value,
            detail={"motivo": reason, "transaccion": str(transaction_id) if transaction_id else None},
        )
        await self.repository.commit()
        return command

    async def recent_commands(self, limit: int = 10) -> list[GateCommand]:
        return await self.repository.recent_commands(limit)

    async def complete_command(self, command_id: UUID, success: bool, error: str | None) -> GateCommand:
        command = await self.repository.find_command(command_id)
        if command is None:
            raise CommandNotFound
        if command.status not in (CommandStatus.PENDING, CommandStatus.SENT):
            return command  # reintento del worker

        command.completed_at = get_localized_now()
        actor = Actor(command.requested_by_username, command.requested_by_id)

        if not success:
            command.status = CommandStatus.FAILED
            command.error = error
            self.repository.add(command)
            self.audit.record(
                AuditAction.GATE_OPEN_FAILED, actor, "gate", command.gate.value, command.gate.value,
                result=AuditResult.FAILURE, detail={"motivo": error or "Sin respuesta de la talanquera"},
            )
            await self.report_event(TechnicalEventIn(
                device_code=GATE_DEVICE[command.gate],
                error_code="GATE_NO_RESPONSE",
                description=error or "La talanquera no respondió a la orden de apertura manual.",
                transaction_id=command.transaction_id,
            ))
            return command

        command.status = CommandStatus.DONE
        self.repository.add(command)
        if command.transaction_id is None:
            self.audit.record(
                AuditAction.GATE_OPENED, actor, "gate", command.gate.value, command.gate.value,
                detail={"talanquera": command.gate.value, "modo": "manual", "motivo": command.reason},
            )
            await self.repository.commit()
        elif command.gate == Gate.ENTRY:
            await self.transaction_service.mark_entry_gate_opened(command.transaction_id, actor, command.reason)
        else:
            await self.transaction_service.confirm_exit(command.transaction_id, actor, command.reason)
        return command

    async def set_display(self, gate: Gate, data: GateDisplayIn) -> None:
        lot = await self.parking_lots.get_default()
        display = await self.repository.find_display(lot.id, gate)
        if display is None:
            display = GateDisplay(parking_lot_id=lot.id, gate=gate)
        display.state = data.state
        display.message = data.message
        display.plate = data.plate
        display.expires_at = get_localized_now() + timedelta(seconds=data.duration_seconds)
        self.repository.add(display)
        await self.repository.commit()

    async def public_display(self, gate: Gate) -> tuple[GateDisplayPublic, Occupancy]:
        lot = await self.parking_lots.get_default()
        occupancy = Occupancy.of(lot.capacity, await self.transactions.count_inside(lot.id))
        display = await self.repository.find_display(lot.id, gate)

        if display is None or display.expires_at is None or display.expires_at < get_localized_now():
            return GateDisplayPublic(gate=gate, state=DisplayState.IDLE, message="", plate=None), occupancy
        return GateDisplayPublic(
            gate=gate, state=display.state, message=display.message, plate=display.plate
        ), occupancy
