from abc import ABC, abstractmethod
from decimal import Decimal

from src.server.payment.domain.payment_attempt import PaymentMethod


class PaymentGateway(ABC):
    """Puerto de la pasarela.

    Para una pasarela real se implementa esta clase y un webhook que verifique la firma y llame
    a `PaymentService.apply_result`; el resto del flujo no cambia.
    """

    name: str
    simulated: bool = False

    @abstractmethod
    def methods(self) -> list[PaymentMethod]: ...

    @abstractmethod
    async def create_payment(self, reference: str, amount: Decimal, method: str, plate: str) -> None:
        """Registra el cobro en la pasarela. Lanza una excepción si no se pudo iniciar."""
