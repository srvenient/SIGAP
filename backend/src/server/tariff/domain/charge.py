"""Cálculo del cobro (HU-07). Funciones puras, sin base de datos ni reloj."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from math import ceil
from typing import Protocol

# Pasadas las 12 h se abre un nuevo período de cobro con otra tarifa plena (documento V2.1).
BILLING_PERIOD_MINUTES = 720


class ChargeMode(str, Enum):
    HOURLY = "hourly"
    FULL_RATE = "full_rate"


class TariffRates(Protocol):
    hourly_rate: Decimal
    fraction_rate: Decimal
    fraction_minutes: int
    full_rate: Decimal
    full_rate_after_minutes: int


@dataclass(frozen=True)
class Charge:
    minutes: int
    amount: Decimal
    mode: ChargeMode
    periods: int = 1


def elapsed_minutes(start: datetime, end: datetime) -> int:
    """Minutos de permanencia: todo minuto iniciado cuenta, con un mínimo de 1."""
    return max(1, ceil((end - start).total_seconds() / 60))


def calculate_charge(tariff: TariffRates, minutes: int) -> Charge:
    if minutes <= tariff.full_rate_after_minutes:
        hours, remainder = divmod(minutes, 60)
        fractions = ceil(remainder / tariff.fraction_minutes)
        amount = hours * Decimal(tariff.hourly_rate) + fractions * Decimal(tariff.fraction_rate)
        return Charge(minutes=minutes, amount=amount, mode=ChargeMode.HOURLY)

    periods = ceil(minutes / BILLING_PERIOD_MINUTES)
    return Charge(
        minutes=minutes,
        amount=periods * Decimal(tariff.full_rate),
        mode=ChargeMode.FULL_RATE,
        periods=periods,
    )
