import re
from dataclasses import dataclass
import easyocr
from loguru import logger

from src.processing.text_cleaner import sanitize_text, format_colombian_plate
from src.server.transaction.domain.transaction import VehicleType

# Patrones estrictos de 6 caracteres para Colombia
CAR_PATTERN = re.compile(r"^[A-Z]{3}\d{3}$")
MOTO_PATTERN = re.compile(r"^[A-Z]{3}\d{2}[A-Z]$")


def identify_vehicle_type(formatted_plate: str) -> VehicleType:
    if not formatted_plate:
        return VehicleType.UNKNOWN

    plate = formatted_plate.replace("-", "").strip().upper()

    if CAR_PATTERN.match(plate):
        return VehicleType.CAR
    if MOTO_PATTERN.match(plate):
        return VehicleType.MOTORCYCLE

    return VehicleType.UNKNOWN


@dataclass(frozen=True)
class PlateReaderResult:
    license_plate: str
    vehicle_type: VehicleType


class PlateReader:
    ALLOWLIST = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    def __init__(self, use_gpu: bool = True):
        logger.info("Inicializando EasyOCR...")
        try:
            self.reader = easyocr.Reader(['en'], gpu=use_gpu)
            if use_gpu:
                logger.success("🚀 EasyOCR inicializado. Usando GPU mediante PyTorch.")
            else:
                logger.info("EasyOCR operando en modo CPU por configuración.")
        except Exception as e:
            logger.error(f"Error inicializando EasyOCR: {e}")
            raise

    def read_text(self, processed_image) -> PlateReaderResult | None:
        if processed_image is None:
            return None

        results = self.reader.readtext(
            processed_image,
            allowlist=self.ALLOWLIST,
            workers=0,
            batch_size=1,
            adjust_contrast=False,
            paragraph=False
        )

        if not results:
            return None

        valid_detections = []
        max_height = 0

        for box, text, confidence in results:
            if confidence > 0.35:
                box_height = abs(box[2][1] - box[0][1])
                if box_height > max_height:
                    max_height = box_height
                valid_detections.append((box, text, confidence, box_height))

        if not valid_detections:
            return None

        main_chars = [det for det in valid_detections if det[3] >= (max_height * 0.50)]
        main_chars.sort(key=lambda item: item[0][0][0])
        raw_text = "".join([item[1] for item in main_chars])

        clean_text = sanitize_text(raw_text)

        # Fast-Fail: Si tiene menos de 6 caracteres alfanuméricos, se descarta de inmediato
        if len(clean_text) < 6:
            return None

        formatted_plate = format_colombian_plate(clean_text)
        final_plate = formatted_plate.replace("-", "")
        vehicle_type = identify_vehicle_type(final_plate)

        if vehicle_type == VehicleType.UNKNOWN:
            logger.debug(f"Lectura descartada por formato inválido: {final_plate}")
            return None

        return PlateReaderResult(license_plate=final_plate, vehicle_type=vehicle_type)