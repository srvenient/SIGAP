from typing import Annotated

from fastapi import Depends

from src.server.payment.application.payment_service import PaymentService
from src.server.shared.api.deps import SessionDep
from src.server.wiring import build_payment_service


def get_payment_service(session: SessionDep) -> PaymentService:
    return build_payment_service(session)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
