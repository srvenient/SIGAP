from typing import Annotated

from fastapi import Depends

from server.transaction.application.transaction_service import TransactionService
from src.server.transaction.domain.transaction_repository import TransactionRepository
from src.server.transaction.infrastructure.postgres_transaction_repository import PostgresTransactionRepository
from src.server.shared.api.deps import SessionDep


def get_transaction_repository(session: SessionDep) -> TransactionRepository:
    return PostgresTransactionRepository(session)


TransactionRepositoryDep = Annotated[PostgresTransactionRepository, Depends(get_transaction_repository)]


def get_transaction_service(transaction_repository: TransactionRepositoryDep) -> TransactionService:
    return TransactionService(transaction_repository)


TransactionServiceDep = Annotated[TransactionService, Depends(get_transaction_service)]
