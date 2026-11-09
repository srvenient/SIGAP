from datetime import datetime
from uuid import UUID

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.payment.domain.payment_attempt import PaymentAttempt, PaymentStatus
from src.server.payment.domain.payment_repository import PaymentRepository


class PostgresPaymentRepository(PaymentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_reference(self, reference: str, for_update: bool = False) -> PaymentAttempt | None:
        statement = select(PaymentAttempt).where(PaymentAttempt.reference == reference)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return (await self.session.exec(statement)).first()

    async def find_pending_of(self, transaction_id: UUID) -> list[PaymentAttempt]:
        result = await self.session.exec(
            select(PaymentAttempt).where(
                PaymentAttempt.transaction_id == transaction_id,
                PaymentAttempt.status == PaymentStatus.PENDING,
            ).with_for_update()
        )
        return list(result.all())

    async def list_of(self, transaction_id: UUID) -> list[PaymentAttempt]:
        result = await self.session.exec(
            select(PaymentAttempt).where(PaymentAttempt.transaction_id == transaction_id)
            .order_by(col(PaymentAttempt.created_at))
        )
        return list(result.all())

    async def lock_overdue(self, cutoff: datetime) -> list[PaymentAttempt]:
        result = await self.session.exec(
            select(PaymentAttempt).where(
                PaymentAttempt.status == PaymentStatus.PENDING,
                col(PaymentAttempt.created_at) < cutoff,
            ).with_for_update(skip_locked=True)
        )
        return list(result.all())

    def add(self, attempt: PaymentAttempt) -> None:
        self.session.add(attempt)

    async def commit(self) -> None:
        await self.session.commit()
