from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.server.tariff.domain.charge import ChargeMode, calculate_charge, elapsed_minutes


@dataclass
class Rates:
    hourly_rate: Decimal = Decimal(4000)
    fraction_rate: Decimal = Decimal(2000)
    fraction_minutes: int = 30
    full_rate: Decimal = Decimal(20000)
    full_rate_after_minutes: int = 300


@pytest.mark.parametrize(
    ("minutes", "amount", "mode", "periods"),
    [
        (1, 2000, ChargeMode.HOURLY, 1),  # una fracción iniciada
        (30, 2000, ChargeMode.HOURLY, 1),
        (31, 4000, ChargeMode.HOURLY, 1),  # dos fracciones
        (60, 4000, ChargeMode.HOURLY, 1),  # hora exacta, sin fracción
        (61, 6000, ChargeMode.HOURLY, 1),  # hora + una fracción
        (299, 20000, ChargeMode.HOURLY, 1),  # 4 h + 2 fracciones
        (300, 20000, ChargeMode.HOURLY, 1),  # el límite aún es por hora
        (301, 20000, ChargeMode.FULL_RATE, 1),
        (720, 20000, ChargeMode.FULL_RATE, 1),  # 12 h: último minuto del primer período
        (721, 40000, ChargeMode.FULL_RATE, 2),  # nuevo período
        (780, 40000, ChargeMode.FULL_RATE, 2),  # 13 h
        (1440, 40000, ChargeMode.FULL_RATE, 2),
        (1441, 60000, ChargeMode.FULL_RATE, 3),
    ],
)
def test_calculate_charge(minutes: int, amount: int, mode: ChargeMode, periods: int) -> None:
    charge = calculate_charge(Rates(), minutes)

    assert charge.amount == Decimal(amount)
    assert charge.mode == mode
    assert charge.periods == periods


def test_limit_is_configurable() -> None:
    assert calculate_charge(Rates(full_rate_after_minutes=120), 121).mode == ChargeMode.FULL_RATE


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (timedelta(0), 1),
        (timedelta(seconds=1), 1),
        (timedelta(seconds=60), 1),
        (timedelta(seconds=61), 2),
        (timedelta(hours=5), 300),
    ],
)
def test_elapsed_minutes(delta: timedelta, expected: int) -> None:
    start = datetime(2026, 1, 1, 8, 0)

    assert elapsed_minutes(start, start + delta) == expected
