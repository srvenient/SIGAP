"""Composición de servicios a partir de una sesión.

La usan tanto las dependencias de FastAPI como las tareas de fondo, que no tienen petición.
"""
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from src.server.audit.application.audit_recorder import AuditRecorder
from src.server.audit.domain.audit_repository import AuditRepository
from src.server.audit.infrastructure.postgres_audit_repository import PostgresAuditRepository
from src.server.device.application.device_service import DeviceService
from src.server.device.infrastructure.postgres_device_repository import PostgresDeviceRepository
from src.server.intervention.application.intervention_service import InterventionService
from src.server.intervention.infrastructure.postgres_alert_repository import PostgresAlertRepository
from src.server.parking.application.parking_service import ParkingService
from src.server.parking.infrastructure.postgres_parking_lot_repository import PostgresParkingLotRepository
from src.server.payment.application.payment_service import PaymentService
from src.server.payment.domain.payment_gateway import PaymentGateway
from src.server.payment.infrastructure.postgres_payment_repository import PostgresPaymentRepository
from src.server.payment.infrastructure.simulated_gateway import SimulatedGateway
from src.server.reporting.application.reporting_service import ReportingService
from src.server.reporting.infrastructure.postgres_report_repository import PostgresReportRepository
from src.server.tariff.application.tariff_service import TariffService
from src.server.tariff.infrastructure.postgres_tariff_repository import PostgresTariffRepository
from src.server.ticket.application.ticket_service import TicketService
from src.server.ticket.infrastructure.postgres_ticket_repository import PostgresTicketRepository
from src.server.transaction.application.transaction_service import TransactionService
from src.server.transaction.infrastructure.postgres_transaction_repository import PostgresTransactionRepository

_GATEWAYS: dict[str, type[PaymentGateway]] = {"simulated": SimulatedGateway}


def build_audit_repository(session: AsyncSession) -> AuditRepository:
    return PostgresAuditRepository(session)


def build_audit_recorder(session: AsyncSession) -> AuditRecorder:
    return AuditRecorder(build_audit_repository(session))


def build_parking_service(session: AsyncSession) -> ParkingService:
    return ParkingService(
        PostgresParkingLotRepository(session),
        PostgresTransactionRepository(session),
        build_audit_recorder(session),
    )


def build_tariff_service(session: AsyncSession) -> TariffService:
    return TariffService(
        PostgresTariffRepository(session),
        PostgresParkingLotRepository(session),
        build_audit_recorder(session),
    )


def build_transaction_service(session: AsyncSession) -> TransactionService:
    return TransactionService(
        PostgresTransactionRepository(session),
        PostgresParkingLotRepository(session),
        build_audit_recorder(session),
    )


def build_payment_service(session: AsyncSession) -> PaymentService:
    return PaymentService(
        PostgresPaymentRepository(session),
        PostgresTransactionRepository(session),
        build_tariff_service(session),
        _GATEWAYS[settings.PAYMENT_GATEWAY](),
        build_audit_recorder(session),
    )


def build_ticket_service(session: AsyncSession) -> TicketService:
    return TicketService(
        PostgresTicketRepository(session),
        PostgresParkingLotRepository(session),
        PostgresTransactionRepository(session),
        build_audit_recorder(session),
    )


def build_device_service(session: AsyncSession) -> DeviceService:
    return DeviceService(
        PostgresDeviceRepository(session),
        PostgresParkingLotRepository(session),
        PostgresTransactionRepository(session),
        build_transaction_service(session),
        build_ticket_service(session),
        build_audit_recorder(session),
    )


def build_intervention_service(session: AsyncSession) -> InterventionService:
    return InterventionService(
        PostgresAlertRepository(session),
        PostgresParkingLotRepository(session),
        build_transaction_service(session),
        build_device_service(session),
        build_audit_recorder(session),
    )


def build_reporting_service(session: AsyncSession) -> ReportingService:
    return ReportingService(
        PostgresReportRepository(session),
        build_parking_service(session),
        build_device_service(session),
    )
