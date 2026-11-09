from datetime import date, datetime, time, timedelta

from src.server.shared.infrastructure.providers.system_clock import TIMEZONE, get_localized_now


def day_bounds(date_from: date | None, date_to: date | None) -> tuple[datetime | None, datetime | None]:
    """Convierte fechas locales en un rango [inicio, fin) con zona horaria; `date_to` es inclusiva."""
    start = datetime.combine(date_from, time.min, TIMEZONE) if date_from else None
    end = datetime.combine(date_to + timedelta(days=1), time.min, TIMEZONE) if date_to else None
    return start, end


def today_bounds() -> tuple[datetime, datetime]:
    today = get_localized_now().date()
    start, end = day_bounds(today, today)
    return start, end  # type: ignore[return-value]
