"""Datos mínimos para operar. Es idempotente: solo crea lo que falta."""
from decimal import Decimal

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core import security
from core.config import settings
from src.server import models  # noqa: F401
from src.server.auth.domain.role.role import ROLE_DESCRIPTIONS, Role, RoleName
from src.server.auth.domain.user.user import User
from src.server.device.domain.device import DEVICE_CATALOG, Device
from src.server.parking.domain.parking_lot import DEFAULT_PARKING_LOT_ID, ParkingLot
from src.server.tariff.domain.tariff import Tariff
from src.server.transaction.domain.plate import VehicleType

# Valores de ejemplo: el Administrador los ajusta desde la plataforma
_DEFAULT_TARIFFS = {
    VehicleType.CAR: (Decimal(4000), Decimal(2000), 30, Decimal(20000)),
    VehicleType.MOTORCYCLE: (Decimal(2000), Decimal(1000), 30, Decimal(10000)),
}


async def seed(session: AsyncSession) -> None:
    lot = await session.get(ParkingLot, DEFAULT_PARKING_LOT_ID)
    if lot is None:
        session.add(ParkingLot(id=DEFAULT_PARKING_LOT_ID, name="Sede principal"))
        await session.flush()

    roles = {r.name: r for r in (await session.exec(select(Role))).all()}
    for role_name in RoleName:
        if role_name.value not in roles:
            role = Role(name=role_name.value, description=ROLE_DESCRIPTIONS[role_name])
            session.add(role)
            roles[role_name.value] = role
    await session.flush()

    superuser = (await session.exec(select(User).where(User.username == settings.FIRST_SUPERUSER))).first()
    if superuser is None:
        # Sin pasar por UserCreate: la contraseña inicial viene del .env y no le aplica la política
        session.add(User(
            username=settings.FIRST_SUPERUSER,
            hashed_password=security.get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            role_id=roles[RoleName.ADMIN.value].id,
        ))

    existing_tariffs = {t.vehicle_type for t in (await session.exec(select(Tariff))).all()}
    for vehicle_type, (hourly, fraction, minutes, full) in _DEFAULT_TARIFFS.items():
        if vehicle_type not in existing_tariffs:
            session.add(Tariff(
                parking_lot_id=DEFAULT_PARKING_LOT_ID,
                vehicle_type=vehicle_type,
                hourly_rate=hourly,
                fraction_rate=fraction,
                fraction_minutes=minutes,
                full_rate=full,
            ))

    existing_devices = {d.code for d in (await session.exec(select(Device))).all()}
    for code, (kind, name) in DEVICE_CATALOG.items():
        if code not in existing_devices:
            session.add(Device(parking_lot_id=DEFAULT_PARKING_LOT_ID, code=code, kind=kind, name=name))

    await session.commit()
