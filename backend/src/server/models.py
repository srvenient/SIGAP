"""Importa todos los modelos para que SQLModel.metadata quede completo (Alembic y pruebas)."""
from src.server.audit.domain.audit_log import AuditLog  # noqa: F401
from src.server.auth.domain.role.role import Role  # noqa: F401
from src.server.auth.domain.token.refresh_token import RefreshToken  # noqa: F401
from src.server.auth.domain.user.user import User  # noqa: F401
from src.server.device.domain.device import Device, GateCommand, GateDisplay, TechnicalEvent  # noqa: F401
from src.server.intervention.domain.alert import AlertSnapshot, OperationAlert  # noqa: F401
from src.server.parking.domain.parking_lot import ParkingLot  # noqa: F401
from src.server.payment.domain.payment_attempt import PaymentAttempt  # noqa: F401
from src.server.tariff.domain.tariff import Tariff, TariffHistory  # noqa: F401
from src.server.ticket.domain.ticket import Ticket, TicketHistory  # noqa: F401
from src.server.transaction.domain.transaction import Transaction  # noqa: F401
