from uuid import UUID
from typing import Optional, List
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.transaction.domain.transaction import Transaction, TransactionStatus
from src.server.transaction.domain.transaction_repository import TransactionRepository


class PostgresTransactionRepository(TransactionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        return await self.session.get(Transaction, transaction_id)

    async def find_active_by_plate(self, plate: str) -> Optional[Transaction]:
        # Busca transacciones que no estén finalizadas para la validación de ingreso y salida
        statement = select(Transaction).where(
            Transaction.plate == plate,
            Transaction.status != TransactionStatus.COMPLETED
        )
        result = await self.session.exec(statement)
        return result.first()

    async def find_all(self, skip: int = 0, limit: int = 50) -> List[Transaction]:
        statement = select(Transaction).offset(skip).limit(limit)
        result = await self.session.exec(statement)
        return result.all()

    async def count(self) -> int:
        statement = select(func.count()).select_from(Transaction)
        result = await self.session.exec(statement)
        return result.one()

    async def save(self, transaction: Transaction) -> Transaction:
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def update(self, transaction_id: UUID, transaction_data: dict) -> Optional[Transaction]:
        transaction = await self.find_by_id(transaction_id)
        if not transaction:
            return None

        for key, value in transaction_data.items():
            setattr(transaction, key, value)

        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction
