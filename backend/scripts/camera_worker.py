import os
import sys
import time

import cv2
import requests
import serial
from loguru import logger
from ultralytics import YOLO

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

from src.inference.detection import Detection
from src.inference.plate_reader import PlateReader

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

# --- CONFIGURACIÓN ARDUINO ---
ARDUINO_PORT = os.getenv("ARDUINO_PORT", "COM3")
ARDUINO_BAUD = int(os.getenv("ARDUINO_BAUD", "9600"))
#
try:
    logger.info(f"Conectando al Arduino en {ARDUINO_PORT}...")
    arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
    time.sleep(2) # Tiempo necesario para que el Arduino se reinicie al abrir el puerto
    logger.success("Conexión Serial establecida con el Arduino.")
except Exception as e:
    logger.error(f"No se pudo conectar al Arduino. Verifica el puerto y la conexión física. Error: {e}")
    arduino = None

ENTRY_DIR = os.path.join(BASE_DIR, "input", "entrada")
EXIT_DIR = os.path.join(BASE_DIR, "input", "salida")
PROCESSED_DIR = os.path.join(BASE_DIR, "input", "procesadas")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

MODEL_PATH = os.path.join(BASE_DIR, "models", "YOLO", "SIGAP_model_small_v1.pt")

for directory in [ENTRY_DIR, EXIT_DIR, PROCESSED_DIR, OUTPUT_DIR]:
    os.makedirs(directory, exist_ok=True)

def open_gate(gate_type: str):
    if arduino and arduino.is_open:
        try:
            command = b'E' if gate_type == "entry" else b'S'
            arduino.write(command)
            logger.info(f"🔌 Señal '{command.decode()}' enviada al Arduino (Talanquera {gate_type.upper()}).")
        except Exception as e:
            logger.error(f"Error al enviar comando al Arduino: {e}")
            # Aquí podrías generar una alerta técnica para el Administrador según la HU-05[cite: 6]
    else:
        logger.warning("Arduino desconectado. No se puede abrir la talanquera físicamente.")


def send_to_backend_with_retry(gate_type: str, plate: str, vehicle_type: str, max_retries: int = 3):
    headers = {"Content-Type": "application/json"}

    v_type_str = vehicle_type.value if hasattr(vehicle_type, 'value') else str(vehicle_type).split('.')[-1].lower()

    for attempt in range(1, max_retries + 1):
        try:
            if gate_type == "entry":
                response = requests.post(
                    url=f"{API_URL}/transactions/entry",
                    json={"plate": plate, "vehicle_type": v_type_str},
                    headers=headers,
                    timeout=5
                )
            else:
                response = requests.post(url=f"{API_URL}/transactions/exit/{plate}", headers=headers, timeout=5)

            if response.status_code in (200, 201):
                logger.success(f"Backend autorizó {gate_type}: {response.json()}")
                open_gate(gate_type)
                # ¡BACKEND AUTORIZÓ! Procedemos a abrir la talanquera[cite: 6, 9]
                # open_barrier(gate_type)
                return True
            else:
                logger.error(f"Backend rechazó {gate_type} ({response.status_code}): {response.text}")
                # No se abre la talanquera si hay error (ej. sin cupo o sin pagar)
                return False

        except requests.exceptions.RequestException as e:
            logger.warning(f"Fallo de conexión (Intento {attempt}/{max_retries}). {e}")
            if attempt < max_retries:
                time.sleep(3)
            else:
                logger.error(f"Se agotaron los intentos de enviar la placa {plate} al backend.")
                return False


def process_image(image_path: str, gate_type: str, filename: str, detection, plate_reader):
    image = cv2.imread(image_path)
    if image is None:
        os.rename(image_path, os.path.join(PROCESSED_DIR, f"error_{filename}"))
        return

    frame = detection.detect(image.copy())
    result = plate_reader.read_text(frame)

    if result and result.license_plate:
        logger.info(f"[{gate_type.upper()}] Placa reconocida: {result.license_plate} | Tipo: {result.vehicle_type}")

        sent_success = send_to_backend_with_retry(
            gate_type=gate_type,
            plate=result.license_plate,
            vehicle_type=result.vehicle_type
        )

        output_path = os.path.join(OUTPUT_DIR, f"detected_{filename}")
        cv2.imwrite(output_path, frame)
    else:
        logger.warning(f"[{gate_type.upper()}] No se reconoció ninguna placa válida en {filename}")

    os.rename(image_path, os.path.join(PROCESSED_DIR, filename))


def watch_directories(detection, plate_reader):
    logger.info("Iniciando monitoreo de cámaras locales (Worker IA con Arduino)...")
    while True:
        try:
            for filename in os.listdir(ENTRY_DIR):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    process_image(os.path.join(ENTRY_DIR, filename), "entry", filename, detection, plate_reader)

            for filename in os.listdir(EXIT_DIR):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    process_image(os.path.join(EXIT_DIR, filename), "exit", filename, detection, plate_reader)

            time.sleep(1)
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            time.sleep(2)


if __name__ == "__main__":
    if not os.path.exists(MODEL_PATH):
        sys.exit(1)

    yolo_model = YOLO(MODEL_PATH)
    object_detection = Detection(yolo_model)
    ocr_reader = PlateReader(use_gpu=True)

    try:
        watch_directories(object_detection, ocr_reader)
    except KeyboardInterrupt:
        if arduino and arduino.is_open:
            arduino.close()
        sys.exit(0)
