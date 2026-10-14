import re
from dataclasses import dataclass

import easyocr
from loguru import logger

from processing.text_cleaner import sanitize_text
from server.transaction.domain.transaction import VehicleType

CAR_PATTERN = re.compile(r"^[A-Z]{3}\d{3}$")
MOTO_PATTERN = re.compile(r"^[A-Z]{3}\d{2}[A-Z]?$")


def identify_vehicle_type(formatted_plate: str) -> VehicleType:
    if not formatted_plate:
        logger.info("Placa vacía o nula, no se puede identificar el tipo de vehículo.")
        return VehicleType.UNKNOWN

    plate = formatted_plate.strip().upper()

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

        # 1. allowlist evita que lea símbolos raros o minúsculas
        results = self.reader.readtext(
            processed_image,
            allowlist=self.ALLOWLIST,
        )

        if not results:
            return None

        # 2. Calcular la altura de cada caja detectada para ignorar "COLOMBIA", "YAMAHA" y el logo
        # box tiene formato: [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
        valid_detections = []
        max_height = 0

        for box, text, confidence in results:
            if confidence > 0.35:
                # Altura de la caja actual
                box_height = abs(box[2][1] - box[0][1])
                if box_height > max_height:
                    max_height = box_height
                valid_detections.append((box, text, confidence, box_height))

        if not valid_detections:
            return None

        # 3. Filtrar: Solo nos quedamos con las cajas que tengan al menos el 50% de la altura
        # de la letra más grande (esto elimina "COLOMBIA", "YAMAHA" y logos pequeños)
        main_chars = [
            det for det in valid_detections
            if det[3] >= (max_height * 0.50)
        ]

        # 4. Ordenar estrictamente de izquierda a derecha según la coordenada X inicial (box[0][0])
        main_chars.sort(key=lambda item: item[0][0][0])

        raw_text = "".join([item[1] for item in main_chars])
        logger.debug(f"Texto crudo filtrado de EasyOCR: {raw_text}")

        if not raw_text:
            return None

        license_plate = sanitize_text(raw_text)

        return PlateReaderResult(license_plate=license_plate, vehicle_type=identify_vehicle_type(license_plate))
