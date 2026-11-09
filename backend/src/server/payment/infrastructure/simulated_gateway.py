from decimal import Decimal

from src.server.payment.domain.payment_attempt import PaymentMethod
from src.server.payment.domain.payment_gateway import PaymentGateway


class SimulatedGateway(PaymentGateway):
    """No cobra dinero real: la respuesta la decide el botón de simulación del módulo de pago."""

    name = "simulated"
    simulated = True

    def methods(self) -> list[PaymentMethod]:
        return [
            PaymentMethod(code="card", label="Tarjeta"),
            PaymentMethod(code="pse", label="PSE"),
            PaymentMethod(code="nequi", label="Nequi"),
        ]

    async def create_payment(self, reference: str, amount: Decimal, method: str, plate: str) -> None:
        return None
