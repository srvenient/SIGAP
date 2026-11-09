from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.transaction.domain.transaction import ACTIVE_STATUSES, AlreadyInside, Transaction
from src.server.transaction.domain.transaction_repository import TransactionFilters, TransactionRepository


class PostgresTransactionRepository(TransactionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, transaction_id: UUID) -> Transaction | None:
        return await self.session.get(Transaction, transaction_id)

    async def find_by_id_for_update(self, transaction_id: UUID) -> Transaction | None:
        return await self.session.get(
            Transaction, transaction_id, with_for_update=True, populate_existing=True
        )

    async def find_active_by_plate(self, plate: str, for_update: bool = False) -> Transaction | None:
        statement = select(Transaction).where(
            Transaction.plate == plate,
            col(Transaction.status).in_(ACTIVE_STATUSES),
        )
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        result = await self.session.exec(statement)
        return result.first()

    async def count_inside(self, parking_lot_id: UUID) -> int:
        result = await self.session.exec(
            select(func.count()).select_from(Transaction).where(
                Transaction.parking_lot_id == parking_lot_id,
                col(Transaction.status).in_(ACTIVE_STATUSES),
            )
        )
        return result.one()

    async def list_inside(self, parking_lot_id: UUID, plate: str | None) -> list[Transaction]:
        statement = select(Transaction).where(
            Transaction.parking_lot_id == parking_lot_id,
            col(Transaction.status).in_(ACTIVE_STATUSES),
        )
        if plate:
            statement = statement.where(col(Transaction.plate).icontains(plate, autoescape=True))
        result = await self.session.exec(statement.order_by(col(Transaction.entry_time).desc()))
        return list(result.all())

    async def search(
            self, filters: TransactionFilters, skip: int, limit: int
    ) -> tuple[list[Transaction], int]:
        conditions = []
        if filters.plate:
            conditions.append(col(Transaction.plate).icontains(filters.plate, autoescape=True))
        if filters.vehicle_type:
            conditions.append(col(Transaction.vehicle_type) == filters.vehicle_type)
        if filters.status:
            conditions.append(col(Transaction.status) == filters.status)
        if filters.start:
            conditions.append(col(Transaction.entry_time) >= filters.start)
        if filters.end:
            conditions.append(col(Transaction.entry_time) < filters.end)

        rows = await self.session.exec(
            select(Transaction).where(*conditions)
            .order_by(col(Transaction.entry_time).desc()).offset(skip).limit(limit)
        )
        total = await self.session.exec(select(func.count()).select_from(Transaction).where(*conditions))
        return list(rows.all()), total.one()

    async def save(self, transaction: Transaction) -> Transaction:
        self.session.add(transaction)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            if "uq_transactions_active_plate" in str(exc.orig):
                raise AlreadyInside from None
            raise
        await self.session.refresh(transaction)
        return transaction
