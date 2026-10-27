import os
import sys
import threading
import time
from datetime import datetime

import cv2
import numpy as np
import requests
import serial
from loguru import logger
from ultralytics import YOLO

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

from src.inference.detection import Detection
from src.inference.plate_reader import PlateReader

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

CAM_ENTRY_INDEX = int(os.getenv("CAM_ENTRY_INDEX", "0"))
CAM_EXIT_INDEX = int(os.getenv("CAM_EXIT_INDEX", "1"))

ARDUINO_PORT = os.getenv("ARDUINO_PORT", "COM3")
ARDUINO_BAUD = int(os.getenv("ARDUINO_BAUD", "9600"))

try:
    logger.info(f"Conectando al Arduino en {ARDUINO_PORT}...")
    arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
    time.sleep(2)
    logger.success("Conexión Serial establecida con el Arduino.")
except Exception as e:
    logger.error(f"No se pudo conectar al Arduino. Verifica el puerto. Error: {e}")
    arduino = None

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
MODEL_PATH = os.path.join(BASE_DIR, "models", "YOLO", "SIGAP_model_small_v1.pt")

plate_buffer = {"entry": [], "exit": []}
REQUIRED_READINGS = 3
BUFFER_TIMEOUT = 2.0
COOLDOWN_SECONDS = 15

last_seen_plates = {
    "entry": {"plate": None, "time": 0},
    "exit": {"plate": None, "time": 0}
}

gate_ui_banner = {
    "entry": {"text": "ESTADO: ESCANEANDO ENTRADA...", "color": (0, 255, 255), "until": 0},
    "exit": {"text": "ESTADO: ESCANEANDO SALIDA...", "color": (0, 255, 255), "until": 0}
}

# Tabla Gamma precalculada en memoria para no recrearla en cada frame nocturno
GAMMA_TABLE = np.array([((i / 255.0) ** (1.0 / 1.5)) * 255 for i in np.arange(0, 256)]).astype("uint8")


def set_ui_banner(gate_type: str, text: str, color: tuple, duration: float = 6.0):
    gate_ui_banner[gate_type] = {
        "text": text,
        "color": color,
        "until": time.time() + duration
    }


def open_gate(gate_type: str):
    if arduino and arduino.is_open:
        try:
            command = b'E' if gate_type == "entry" else b'S'
            arduino.write(command)
            logger.info(f"🔌 Señal '{command.decode()}' enviada al Arduino (Talanquera {gate_type.upper()}).")
        except Exception as e:
            logger.error(f"Error al enviar comando al Arduino: {e}")
    else:
        logger.warning("Arduino desconectado. No se puede abrir la talanquera.")


def send_to_backend_with_retry(gate_type: str, plate: str, vehicle_type: str, max_retries: int = 3):
    headers = {"Content-Type": "application/json"}
    v_type_str = vehicle_type.value if hasattr(vehicle_type, 'value') else str(vehicle_type).split('.')[-1].lower()

    set_ui_banner(gate_type, f"VALIDANDO EN SERVIDOR: {plate}...", (255, 255, 0), duration=5.0)

    for attempt in range(1, max_retries + 1):
        try:
            url = f"{API_URL}/transactions/entry" if gate_type == "entry" else f"{API_URL}/transactions/exit/{plate}"
            payload = {"plate": plate, "vehicle_type": v_type_str} if gate_type == "entry" else None

            response = requests.post(url=url, json=payload, headers=headers, timeout=5)

            if response.status_code in (200, 201):
                logger.success(f"[{gate_type.upper()}] Backend autorizó {plate}: {response.json()}")
                set_ui_banner(gate_type, f"AUTORIZADO: {plate} - ABRIENDO", (0, 255, 0), duration=6.0)
                open_gate(gate_type)
                return True

            try:
                error_detail = response.json().get("detail", "Operación no autorizada")
            except Exception:
                error_detail = response.text

            if response.status_code == 400:
                logger.warning(f"[{gate_type.upper()}] Rechazo 400 ({plate}): {error_detail}")
                set_ui_banner(gate_type, f"DENEGADO: {plate} YA ESTA ADENTRO", (0, 0, 255), duration=7.0)
                return False

            if response.status_code == 402:
                logger.warning(f"[{gate_type.upper()}] Rechazo 402 ({plate}): {error_detail}")
                set_ui_banner(gate_type, f"DENEGADO: PAGO PENDIENTE ({plate})", (0, 0, 255), duration=8.0)
                return False

            if response.status_code == 404:
                logger.warning(f"[{gate_type.upper()}] Rechazo 404 ({plate}): {error_detail}")
                set_ui_banner(gate_type, f"DENEGADO: SIN ENTRADA ({plate})", (0, 0, 255), duration=7.0)
                return False

            # Otros errores (ej. 422 o 500)
            logger.error(f"[{gate_type.upper()}] Error HTTP {response.status_code}: {error_detail}")
            if response.status_code < 500:
                set_ui_banner(gate_type, f"ERROR ({response.status_code}): {plate}", (0, 0, 255), duration=6.0)
                return False

        except requests.exceptions.RequestException as e:
            logger.warning(f"[{gate_type.upper()}] Fallo de red (Intento {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(2)
            else:
                set_ui_banner(gate_type, "ERROR DE CONEXION CON SERVIDOR", (0, 0, 255), duration=6.0)
                return False


def apply_night_vision(frame):
    gamma_corrected = cv2.LUT(frame, GAMMA_TABLE)
    lab = cv2.cvtColor(gamma_corrected, cv2.COLOR_BGR2LAB)
    l_channel, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    cl = clahe.apply(l_channel)

    merged = cv2.merge((cl, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def draw_top_banner(display_frame, gate_type: str):
    current_time = time.time()
    banner = gate_ui_banner[gate_type]

    if current_time < banner["until"]:
        text = banner["text"]
        color = banner["color"]
    else:
        label = "ENTRADA" if gate_type == "entry" else "SALIDA"
        text = f"ESTADO ({label}): ESCANEANDO..."
        color = (0, 255, 255)

    # Barra superior oscura para legibilidad
    cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], 50), (20, 20, 20), -1)
    cv2.putText(display_frame, text, (15, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)


def process_frame(frame, gate_type: str, detection, plate_reader):
    display_frame = frame.copy()

    try:
        current_hour = datetime.now().hour
        is_night = current_hour >= 18 or current_hour < 6

        frame_to_process = apply_night_vision(frame.copy()) if is_night else frame.copy()
        processed_plate, bbox = detection.detect(frame_to_process)

        if processed_plate is not None and bbox is not None:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 165, 255), 2)

            result = plate_reader.read_text(processed_plate)

            if result and result.license_plate:
                plate = result.license_plate
                current_time = time.time()

                # Limpiar lecturas antiguas del búfer de esta cámara
                plate_buffer[gate_type] = [
                    (p, t) for p, t in plate_buffer[gate_type]
                    if current_time - t <= BUFFER_TIMEOUT
                ]

                plate_buffer[gate_type].append((plate, current_time))
                occurrences = sum(1 for p, t in plate_buffer[gate_type] if p == plate)

                texto_estado = f"{plate} ({occurrences}/{REQUIRED_READINGS})"
                color_caja = (0, 165, 255)

                if occurrences >= REQUIRED_READINGS:
                    texto_estado = f"LEIDA: {plate} ({result.vehicle_type.value.upper()})"
                    color_caja = (0, 255, 0)

                    last_plate = last_seen_plates[gate_type]["plate"]
                    time_since_last = current_time - last_seen_plates[gate_type]["time"]

                    if not (last_plate == plate and time_since_last < COOLDOWN_SECONDS):
                        logger.info(f"[{gate_type.upper()}] 🏆 PLACA CONFIRMADA POR CONSENSO: {plate}")
                        last_seen_plates[gate_type] = {"plate": plate, "time": current_time}
                        plate_buffer[gate_type].clear()

                        # Guardar evidencia antes de enviar
                        output_path = os.path.join(OUTPUT_DIR, f"detected_{gate_type}_{plate}_{int(current_time)}.jpg")
                        cv2.imwrite(output_path, display_frame)

                        threading.Thread(
                            target=send_to_backend_with_retry,
                            args=(gate_type, plate, result.vehicle_type),
                            daemon=True
                        ).start()

                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color_caja, 3)
                y_text_bg = max(55, y1 - 35)
                cv2.rectangle(display_frame, (x1, y_text_bg), (x1 + 340, y_text_bg + 35), (0, 0, 0), -1)
                cv2.putText(display_frame, texto_estado, (x1 + 5, y_text_bg + 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_caja, 2)

        draw_top_banner(display_frame, gate_type)
        return display_frame

    except Exception as e:
        logger.error(f"Error interno procesando frame de {gate_type}: {e}")
        draw_top_banner(display_frame, gate_type)
        return display_frame


class CameraReader:
    """Hilo Productor independiente con reconexión automática en segundo plano."""

    def __init__(self, src: int, name: str):
        self.src = src
        self.name = name
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_DSHOW)
        self.ret, self.frame = self.cap.read()
        self.running = True
        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        while self.running:
            if not self.cap.isOpened():
                time.sleep(2.0)
                self.cap = cv2.VideoCapture(self.src, cv2.CAP_DSHOW)
                continue

            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.ret, self.frame = True, frame
            else:
                self.ret = False
                time.sleep(0.1)

    def read(self):
        return self.ret, self.frame

    def release(self):
        self.running = False
        self.thread.join(timeout=1.0)
        if self.cap.isOpened():
            self.cap.release()


def process_streams(detection, plate_reader):
    logger.info(f"Iniciando monitoreo dual -> Entrada (Idx: {CAM_ENTRY_INDEX}) | Salida (Idx: {CAM_EXIT_INDEX})")

    cam_entry = CameraReader(CAM_ENTRY_INDEX, "Entrada")
    cam_exit = CameraReader(CAM_EXIT_INDEX, "Salida")

    TARGET_FPS = 30
    frame_delay = 1.0 / TARGET_FPS

    while True:
        start_time = time.time()

        # 1. Procesar Cámara de Entrada
        ret_in, frame_in = cam_entry.read()
        if ret_in and frame_in is not None:
            processed_in = process_frame(frame_in, "entry", detection, plate_reader)
            cv2.imshow('Entrada - Monitor de Parqueadero', processed_in)

        # 2. Procesar Cámara de Salida (Independiente: si no está conectada, no bloquea la entrada)
        ret_out, frame_out = cam_exit.read()
        if ret_out and frame_out is not None:
            processed_out = process_frame(frame_out, "exit", detection, plate_reader)
            cv2.imshow('Salida - Monitor de Parqueadero', processed_out)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            logger.info("Cierre manual solicitado por el usuario (tecla Q).")
            break

        elapsed = time.time() - start_time
        sleep_time = max(0.0, frame_delay - elapsed)
        if sleep_time > 0:
            time.sleep(sleep_time)

    cam_entry.release()
    cam_exit.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    if not os.path.exists(MODEL_PATH):
        logger.error(f"Modelo no encontrado en {MODEL_PATH}")
        sys.exit(1)

    yolo_model = YOLO(MODEL_PATH)
    object_detection = Detection(yolo_model)
    ocr_reader = PlateReader(use_gpu=True)

    try:
        process_streams(object_detection, ocr_reader)
    except KeyboardInterrupt:
        logger.info("Interrupción manual detectada.")
    finally:
        if arduino and arduino.is_open:
            arduino.close()
        sys.exit(0)