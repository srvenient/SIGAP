from datetime import datetime

from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.reporting.domain.report import Revenue, RevenueLine
from src.server.reporting.domain.report_repository import ReportRepository
from src.server.transaction.domain.transaction import Transaction, TransactionStatus

# HU-19: el recaudo solo considera transacciones en estado Pagado o Finalizado
_COLLECTED = (TransactionStatus.PAID, TransactionStatus.COMPLETED)


class PostgresReportRepository(ReportRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _grouped(self, column, conditions: list) -> list[RevenueLine]:
        rows = await self.session.exec(
            select(column, func.coalesce(func.sum(Transaction.total_amount), 0), func.count())
            .where(*conditions).group_by(column).order_by(column)
        )
        return [
            RevenueLine(key=getattr(key, "value", key) or "sin_dato", total=float(total), count=count)
            for key, total, count in rows.all()
        ]

    async def revenue(self, start: datetime | None, end: datetime | None) -> Revenue:
        conditions = [col(Transaction.status).in_(_COLLECTED), col(Transaction.paid_at).is_not(None)]
        if start:
            conditions.append(col(Transaction.paid_at) >= start)
        if end:
            conditions.append(col(Transaction.paid_at) < end)

        by_type = await self._grouped(col(Transaction.vehicle_type), conditions)
        by_method = await self._grouped(col(Transaction.payment_method), conditions)
        return Revenue(
            total=sum(line.total for line in by_type),
            count=sum(line.count for line in by_type),
            by_vehicle_type=by_type,
            by_payment_method=by_method,
        )

    async def count_entries(self, start: datetime, end: datetime) -> int:
        result = await self.session.exec(
            select(func.count()).select_from(Transaction)
            .where(col(Transaction.entry_time) >= start, col(Transaction.entry_time) < end)
        )
        return result.one()

    async def count_exits(self, start: datetime, end: datetime) -> int:
        result = await self.session.exec(
            select(func.count()).select_from(Transaction)
            .where(col(Transaction.exit_time) >= start, col(Transaction.exit_time) < end)
        )
        return result.one()
