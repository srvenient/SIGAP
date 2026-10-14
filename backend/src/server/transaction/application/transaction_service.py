from fastapi import HTTPException, status

from src.server.transaction.domain.transaction import TransactionCreate, Transaction, TransactionStatus
from src.server.transaction.domain.transaction_repository import TransactionRepository
from src.server.shared.infrastructure.providers.system_clock import get_localized_now


class TransactionService:
    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    async def register_entry(self, data: TransactionCreate) -> Transaction:
        # Validación de duplicidad: Verifica que no exista una transacción activa asociada a la placa
        active_transaction = await self.repository.find_active_by_plate(data.plate)
        if active_transaction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una transacción activa para la placa {data.plate}"
            )

        # Creación de transacción con estado inicial "Ingresado"
        new_transaction = Transaction(
            plate=data.plate,
            vehicle_type=data.vehicle_type,
            status=TransactionStatus.ENTERED
        )
        return await self.repository.save(new_transaction)

    async def process_payment(self, plate: str, amount: float, method: str, reference: str) -> Transaction:
        # Identifica la transacción (por placa) que se encuentra en estado Ingresado
        transaction = await self.repository.find_active_by_plate(plate)
        if not transaction or transaction.status != TransactionStatus.ENTERED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró una transacción pendiente de pago para esta placa"
            )

        # Actualiza la transacción al estado "Pagado" tras confirmación de la pasarela
        update_data = {
            "status": TransactionStatus.PAID,
            "total_amount": amount,
            "payment_method": method,
            "payment_reference": reference
        }
        return await self.repository.update(transaction.id, update_data)

    async def register_exit(self, plate: str) -> Transaction:
        # Busca la transacción y verifica su estado
        transaction = await self.repository.find_active_by_plate(plate)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existe transacción activa para esta placa. Salida no autorizada."
            )

        if transaction.status != TransactionStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="El pago está pendiente. Salida no autorizada."
            )

        # Al confirmarse el estado "Pagado", se actualiza a "Finalizado" y se registra la hora de salida
        update_data = {
            "status": TransactionStatus.COMPLETED,
            "exit_time": get_localized_now()
        }
        return await self.repository.update(transaction.id, update_data)