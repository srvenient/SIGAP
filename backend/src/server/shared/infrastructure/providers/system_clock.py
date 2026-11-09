from datetime import datetime
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("America/Bogota")


def get_localized_now() -> datetime:
    return datetime.now(TIMEZONE)
