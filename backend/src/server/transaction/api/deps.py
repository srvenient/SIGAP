from typing import Annotated

from fastapi import Depends

from src.server.shared.api.deps import SessionDep
from src.server.transaction.application.transaction_service import TransactionService
from src.server.wiring import build_transaction_service


def get_transaction_service(session: SessionDep) -> TransactionService:
    return build_transaction_service(session)


TransactionServiceDep = Annotated[TransactionService, Depends(get_transaction_service)]
