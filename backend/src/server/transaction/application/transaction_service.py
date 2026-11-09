from uuid import UUID

from src.server.audit.application.audit_recorder import AuditRecorder
from src.server.audit.domain.audit_log import SYSTEM, Actor, AuditAction
from src.server.parking.domain.parking_lot_repository import ParkingLotRepository
from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.transaction.domain.plate import VehicleType, identify_vehicle_type, normalize_plate
from src.server.transaction.domain.transaction import (
    AlreadyInside,
    InvalidPlate,
    InvalidTransactionState,
    NoActiveTransaction,
    ParkingFull,
    PaymentPending,
    Transaction,
    TransactionNotFound,
    TransactionStatus,
)
from src.server.transaction.domain.transaction_repository import TransactionFilters, TransactionRepository


def validated_plate(plate: str, vehicle_type: VehicleType | None = None) -> tuple[str, VehicleType]:
    """Normaliza la placa y exige que su formato corresponda al tipo de vehículo (HU-03)."""
    normalized = normalize_plate(plate)
    detected = identify_vehicle_type(normalized)
    if detected == VehicleType.UNKNOWN or (vehicle_type is not None and detected != vehicle_type):
        raise InvalidPlate
    return normalized, detected


class TransactionService:
    def __init__(
            self,
            repository: TransactionRepository,
            parking_lots: ParkingLotRepository,
            audit: AuditRecorder,
    ):
        self.repository = repository
        self.parking_lots = parking_lots
        self.audit = audit

    async def get(self, transaction_id: UUID) -> Transaction:
        transaction = await self.repository.find_by_id(transaction_id)
        if transaction is None:
            raise TransactionNotFound
        return transaction

    async def search(self, filters: TransactionFilters, skip: int, limit: int) -> tuple[list[Transaction], int]:
        return await self.repository.search(filters, skip, limit)

    async def list_inside(self, plate: str | None) -> list[Transaction]:
        lot = await self.parking_lots.get_default()
        return await self.repository.list_inside(lot.id, normalize_plate(plate) if plate else None)

    async def register_entry(
            self,
            plate: str,
            vehicle_type: VehicleType | None,
            actor: Actor = SYSTEM,
            manual_reason: str | None = None,
    ) -> tuple[Transaction, bool]:
        """Crea el ingreso. Devuelve (transacción, creada).

        `creada` es False si la transacción ya existía pero su talanquera nunca confirmó la
        apertura: así el reintento puede volver a abrir en lugar de dejar al conductor afuera.
        """
        plate, detected_type = validated_plate(plate, vehicle_type)

        # El bloqueo dura hasta el commit: dos ingresos simultáneos no pueden tomar el último cupo
        lot = await self.parking_lots.get_default_for_update()

        active = await self.repository.find_active_by_plate(plate)
        if active is not None:
            if active.status == TransactionStatus.ENTERED and active.entry_gate_opened_at is None:
                return active, False
            raise AlreadyInside

        if await self.repository.count_inside(lot.id) >= lot.capacity:
            raise ParkingFull

        transaction = Transaction(
            parking_lot_id=lot.id,
            plate=plate,
            vehicle_type=detected_type,
            manual_intervention=manual_reason is not None,
            manual_reason=manual_reason,
        )
        self.audit.record(
            AuditAction.TRANSACTION_CREATED, actor, "transaction", transaction.id, plate,
            detail={"tipo": detected_type.value, "manual": manual_reason is not None, "motivo": manual_reason},
        )
        return await self.repository.save(transaction), True

    async def mark_entry_gate_opened(
            self, transaction_id: UUID, actor: Actor = SYSTEM, reason: str | None = None
    ) -> Transaction:
        transaction = await self.repository.find_by_id_for_update(transaction_id)
        if transaction is None:
            raise TransactionNotFound
        if transaction.entry_gate_opened_at is not None:
            return transaction

        transaction.entry_gate_opened_at = get_localized_now()
        self.audit.record(
            AuditAction.GATE_OPENED, actor, "transaction", transaction.id, transaction.plate,
            detail={"talanquera": "entry", "modo": "manual" if reason else "automatica", "motivo": reason},
        )
        return await self.repository.save(transaction)

    async def authorize_exit(self, plate: str) -> Transaction:
        """Valida sin cambiar estado: Finalizado solo se registra si la talanquera abrió (HU-12)."""
        transaction = await self.repository.find_active_by_plate(normalize_plate(plate))
        if transaction is None:
            raise NoActiveTransaction
        if transaction.status != TransactionStatus.PAID:
            raise PaymentPending
        return transaction

    async def confirm_exit(
            self, transaction_id: UUID, actor: Actor = SYSTEM, reason: str | None = None
    ) -> Transaction:
        transaction = await self.repository.find_by_id_for_update(transaction_id)
        if transaction is None:
            raise TransactionNotFound
        if transaction.status == TransactionStatus.COMPLETED:
            return transaction  # reintento del worker tras un fallo de red
        if transaction.status != TransactionStatus.PAID:
            raise InvalidTransactionState("Solo se puede finalizar una transacción pagada")

        transaction.status = TransactionStatus.COMPLETED
        transaction.exit_time = get_localized_now()
        mode = {"talanquera": "exit", "modo": "manual" if reason else "automatica", "motivo": reason}
        self.audit.record(
            AuditAction.GATE_OPENED, actor, "transaction", transaction.id, transaction.plate, detail=mode
        )
        self.audit.record(
            AuditAction.TRANSACTION_COMPLETED, actor, "transaction", transaction.id, transaction.plate
        )
        return await self.repository.save(transaction)

    async def flag_manual_intervention(self, transaction: Transaction, reason: str) -> Transaction:
        transaction.manual_intervention = True
        transaction.manual_reason = reason
        return await self.repository.save(transaction)

    async def correct_plate(self, transaction_id: UUID, new_plate: str, reason: str, actor: Actor) -> Transaction:
        """Corrige la placa de un vehículo que sigue dentro (HU-06)."""
        transaction = await self.repository.find_by_id_for_update(transaction_id)
        if transaction is None:
            raise TransactionNotFound
        if transaction.status == TransactionStatus.COMPLETED:
            raise InvalidTransactionState("No se puede corregir una transacción finalizada")

        plate, vehicle_type = validated_plate(new_plate)
        previous = transaction.plate
        if plate != previous and await self.repository.find_active_by_plate(plate) is not None:
            raise AlreadyInside

        transaction.plate = plate
        transaction.vehicle_type = vehicle_type
        transaction.manual_intervention = True
        transaction.manual_reason = reason
        self.audit.record(
            AuditAction.PLATE_CORRECTED, actor, "transaction", transaction.id, plate,
            detail={"anterior": previous, "nueva": plate, "motivo": reason},
        )
        return await self.repository.save(transaction)
