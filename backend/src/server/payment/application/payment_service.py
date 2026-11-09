import secrets
from datetime import timedelta
from uuid import UUID

from core.config import settings
from src.server.audit.application.audit_recorder import AuditRecorder
from src.server.audit.domain.audit_log import DRIVER, SYSTEM, Actor, AuditAction, AuditResult
from src.server.payment.domain.payment_attempt import (
    AlreadyPaid,
    InvalidPaymentMethod,
    NothingToPay,
    PaymentAttempt,
    PaymentMethods,
    PaymentNotFound,
    PaymentState,
    PaymentStatus,
    Quote,
)
from src.server.payment.domain.payment_gateway import PaymentGateway
from src.server.payment.domain.payment_repository import PaymentRepository
from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.tariff.application.tariff_service import TariffService
from src.server.tariff.domain.charge import calculate_charge, elapsed_minutes
from src.server.transaction.domain.plate import normalize_plate
from src.server.transaction.domain.transaction import Transaction, TransactionStatus
from src.server.transaction.domain.transaction_repository import TransactionRepository

_FAILURE_REASONS = {
    PaymentStatus.REJECTED: "Pago rechazado por la pasarela",
    PaymentStatus.CANCELLED: "Pago cancelado por el conductor",
    PaymentStatus.EXPIRED: "Se agotó el tiempo de espera",
}


class PaymentService:
    def __init__(
            self,
            repository: PaymentRepository,
            transactions: TransactionRepository,
            tariffs: TariffService,
            gateway: PaymentGateway,
            audit: AuditRecorder,
    ):
        self.repository = repository
        self.transactions = transactions
        self.tariffs = tariffs
        self.gateway = gateway
        self.audit = audit

    def methods(self) -> PaymentMethods:
        return PaymentMethods(methods=self.gateway.methods(), simulated=self.gateway.simulated)

    async def attempts_of(self, transaction_id: UUID) -> list[PaymentAttempt]:
        return await self.repository.list_of(transaction_id)

    async def _liquidate(self, transaction: Transaction):
        tariff = await self.tariffs.get_current(transaction.vehicle_type)
        minutes = elapsed_minutes(transaction.entry_time, get_localized_now())
        return tariff, calculate_charge(tariff, minutes)

    async def quote(self, plate: str) -> Quote:
        transaction = await self.transactions.find_active_by_plate(normalize_plate(plate))
        if transaction is None:
            raise NothingToPay

        if transaction.status == TransactionStatus.PAID:
            return Quote(
                plate=transaction.plate,
                vehicle_type=transaction.vehicle_type,
                status=transaction.status,
                entry_time=transaction.entry_time,
                minutes=transaction.billed_minutes or 0,
                amount=float(transaction.total_amount or 0),
            )

        _, charge = await self._liquidate(transaction)
        return Quote(
            plate=transaction.plate,
            vehicle_type=transaction.vehicle_type,
            status=transaction.status,
            entry_time=transaction.entry_time,
            minutes=charge.minutes,
            amount=float(charge.amount),
            charge_mode=charge.mode.value,
            periods=charge.periods,
        )

    async def start(self, plate: str, method: str) -> PaymentState:
        if method not in {m.code for m in self.gateway.methods()}:
            raise InvalidPaymentMethod

        transaction = await self.transactions.find_active_by_plate(normalize_plate(plate), for_update=True)
        if transaction is None:
            raise NothingToPay
        if transaction.status == TransactionStatus.PAID:
            raise AlreadyPaid

        # Un intento nuevo reemplaza al anterior que siguiera abierto
        for previous in await self.repository.find_pending_of(transaction.id):
            self._close_failed(previous, transaction, PaymentStatus.EXPIRED, SYSTEM)

        tariff, charge = await self._liquidate(transaction)
        attempt = PaymentAttempt(
            transaction_id=transaction.id,
            reference=f"SGP-{secrets.token_urlsafe(18)}",
            gateway=self.gateway.name,
            method=method,
            amount=charge.amount,
            billed_minutes=charge.minutes,
            tariff_snapshot=tariff.snapshot(),
        )
        await self.gateway.create_payment(attempt.reference, attempt.amount, method, transaction.plate)
        self.repository.add(attempt)
        await self.repository.commit()
        return self._state(attempt, transaction)

    async def state(self, reference: str) -> PaymentState:
        attempt = await self.repository.find_by_reference(reference)
        if attempt is None:
            raise PaymentNotFound
        transaction = await self.transactions.find_by_id(attempt.transaction_id)
        return self._state(attempt, transaction)  # type: ignore[arg-type]

    async def apply_result(
            self, reference: str, approved: bool, reason: str | None = None, actor: Actor = SYSTEM
    ) -> PaymentState:
        """Aplica la respuesta de la pasarela. Es idempotente, como exigen los webhooks."""
        attempt = await self.repository.find_by_reference(reference, for_update=True)
        if attempt is None:
            raise PaymentNotFound
        transaction = await self.transactions.find_by_id_for_update(attempt.transaction_id)
        assert transaction is not None

        if attempt.status != PaymentStatus.PENDING:
            return self._state(attempt, transaction)

        if self._is_overdue(attempt):
            self._close_failed(attempt, transaction, PaymentStatus.EXPIRED, SYSTEM)
        elif approved:
            self._approve(attempt, transaction, actor)
        else:
            self._close_failed(attempt, transaction, PaymentStatus.REJECTED, actor, reason)

        await self.repository.commit()
        return self._state(attempt, transaction)

    async def cancel(self, reference: str) -> PaymentState:
        attempt = await self.repository.find_by_reference(reference, for_update=True)
        if attempt is None:
            raise PaymentNotFound
        transaction = await self.transactions.find_by_id(attempt.transaction_id)
        assert transaction is not None

        if attempt.status == PaymentStatus.PENDING:
            self._close_failed(attempt, transaction, PaymentStatus.CANCELLED, DRIVER)
            await self.repository.commit()
        return self._state(attempt, transaction)

    async def expire_overdue(self) -> int:
        """Cierra los intentos sin respuesta aunque el conductor haya abandonado el módulo."""
        cutoff = get_localized_now() - timedelta(seconds=settings.PAYMENT_TIMEOUT_SECONDS)
        overdue = await self.repository.lock_overdue(cutoff)
        for attempt in overdue:
            transaction = await self.transactions.find_by_id(attempt.transaction_id)
            assert transaction is not None
            self._close_failed(attempt, transaction, PaymentStatus.EXPIRED, SYSTEM)
        await self.repository.commit()
        return len(overdue)

    def _approve(self, attempt: PaymentAttempt, transaction: Transaction, actor: Actor) -> None:
        now = get_localized_now()
        attempt.status = PaymentStatus.APPROVED
        attempt.resolved_at = now

        transaction.status = TransactionStatus.PAID
        transaction.total_amount = attempt.amount
        transaction.billed_minutes = attempt.billed_minutes
        transaction.tariff_snapshot = attempt.tariff_snapshot
        transaction.payment_method = attempt.method
        transaction.payment_reference = attempt.reference
        transaction.paid_at = now

        self.repository.add(attempt)
        self.audit.record(
            AuditAction.PAYMENT_APPROVED, actor, "transaction", transaction.id, transaction.plate,
            detail={"medio": attempt.method, "referencia": attempt.reference, "valor": float(attempt.amount)},
        )

    def _close_failed(
            self,
            attempt: PaymentAttempt,
            transaction: Transaction,
            status: PaymentStatus,
            actor: Actor,
            reason: str | None = None,
    ) -> None:
        """Registra el intento fallido; la transacción permanece en Ingresado (HU-09)."""
        attempt.status = status
        attempt.failure_reason = reason or _FAILURE_REASONS[status]
        attempt.resolved_at = get_localized_now()
        self.repository.add(attempt)
        self.audit.record(
            AuditAction.PAYMENT_FAILED, actor, "transaction", transaction.id, transaction.plate,
            result=AuditResult.FAILURE,
            detail={
                "medio": attempt.method,
                "referencia": attempt.reference,
                "motivo": attempt.failure_reason,
            },
        )

    @staticmethod
    def _is_overdue(attempt: PaymentAttempt) -> bool:
        limit = attempt.created_at + timedelta(seconds=settings.PAYMENT_TIMEOUT_SECONDS)
        return get_localized_now() > limit

    def _state(self, attempt: PaymentAttempt, transaction: Transaction) -> PaymentState:
        return PaymentState(
            reference=attempt.reference,
            plate=transaction.plate,
            method=attempt.method,
            amount=float(attempt.amount),
            status=attempt.status,
            failure_reason=attempt.failure_reason,
            expires_at=attempt.created_at + timedelta(seconds=settings.PAYMENT_TIMEOUT_SECONDS),
            simulated=self.gateway.simulated,
        )
