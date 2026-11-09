from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.server.payment.domain.payment_attempt import PaymentAttempt


class PaymentRepository(ABC):
    @abstractmethod
    async def find_by_reference(self, reference: str, for_update: bool = False) -> PaymentAttempt | None: ...

    @abstractmethod
    async def find_pending_of(self, transaction_id: UUID) -> list[PaymentAttempt]: ...

    @abstractmethod
    async def list_of(self, transaction_id: UUID) -> list[PaymentAttempt]: ...

    @abstractmethod
    async def lock_overdue(self, cutoff: datetime) -> list[PaymentAttempt]:
        """Pendientes creados antes de `cutoff`. Salta los bloqueados por otro proceso."""

    @abstractmethod
    def add(self, attempt: PaymentAttempt) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...
