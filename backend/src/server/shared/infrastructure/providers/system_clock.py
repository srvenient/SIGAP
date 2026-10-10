from datetime import datetime
from zoneinfo import ZoneInfo


def get_localized_now() -> datetime:
    return datetime.now(ZoneInfo("America/Bogota"))
