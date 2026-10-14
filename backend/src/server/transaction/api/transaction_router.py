from fastapi import APIRouter, status

from src.server.transaction.api.deps import TransactionServiceDep
from src.server.transaction.domain.transaction import TransactionPublic, TransactionCreate

transaction_router = APIRouter(prefix="/transactions", tags=["Transactions"])


@transaction_router.post("/entry", response_model=TransactionPublic, status_code=status.HTTP_201_CREATED)
async def create_entry(
        data: TransactionCreate,
        transaction_service: TransactionServiceDep
):
    return await transaction_service.register_entry(data)


@transaction_router.post("/exit/{plate}", response_model=TransactionPublic)
async def process_exit(
        plate: str,
        transaction_service: TransactionServiceDep
):
    return await transaction_service.register_exit(plate)
