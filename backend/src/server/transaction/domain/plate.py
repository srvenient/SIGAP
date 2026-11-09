import re
from enum import Enum


class VehicleType(str, Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    UNKNOWN = "unknown"


# Formatos de placa colombiana (6 caracteres)
CAR_PATTERN = re.compile(r"^[A-Z]{3}\d{3}$")
MOTO_PATTERN = re.compile(r"^[A-Z]{3}\d{2}[A-Z]$")


def normalize_plate(value: str) -> str:
    return "".join(value.split()).upper().replace("-", "")


def identify_vehicle_type(plate: str) -> VehicleType:
    if not plate:
        return VehicleType.UNKNOWN

    normalized = normalize_plate(plate)
    if CAR_PATTERN.match(normalized):
        return VehicleType.CAR
    if MOTO_PATTERN.match(normalized):
        return VehicleType.MOTORCYCLE
    return VehicleType.UNKNOWN
