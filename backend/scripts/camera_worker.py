import base64
import os
import sys
import threading
import time
from datetime import datetime

import cv2
import numpy as np
from loguru import logger
from ultralytics import YOLO

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

from src.inference.detection import Detection
from src.inference.plate_reader import PlateReader
from src.worker.backend_client import BackendClient
from src.worker.gate_controller import GateController
from src.worker.gate_flow import GateFlow, Notice

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
DEVICE_API_KEY = os.getenv("DEVICE_API_KEY", "")

# --- CONFIGURACIÓN CÁMARAS (WINDOWS) ---
CAM_ENTRY_INDEX = int(os.getenv("CAM_ENTRY_INDEX", "1"))
CAM_EXIT_INDEX = int(os.getenv("CAM_EXIT_INDEX", "2"))

# --- CONFIGURACIÓN ARDUINO ---
ARDUINO_PORT = os.getenv("ARDUINO_PORT", "COM3")
ARDUINO_BAUD = int(os.getenv("ARDUINO_BAUD", "9600"))

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
MODEL_PATH = os.path.join(BASE_DIR, "models", "YOLO", "SIGAP_model_small_v1.pt")

# --- VARIABLES DE ESTADO Y CONSENSO ---
plate_buffer = {"entry": [], "exit": []}
REQUIRED_READINGS = 3
BUFFER_TIMEOUT = 2.0
COOLDOWN_SECONDS = 15

last_seen_plates = {
    "entry": {"plate": None, "time": 0},
    "exit": {"plate": None, "time": 0}
}

# --- PLACA NO RECONOCIDA (HU-01) ---
UNREADABLE_AFTER_SECONDS = 4.0
UNREADABLE_COOLDOWN_SECONDS = 30.0
SNAPSHOT_MAX_WIDTH = 640

read_attempt = {"entry": {"since": 0.0, "last": 0.0}, "exit": {"since": 0.0, "last": 0.0}}
last_unreadable_alert = {"entry": 0.0, "exit": 0.0}

HEARTBEAT_SECONDS = 5.0

COLOR_SCANNING = (0, 255, 255)
STATE_COLORS = {
    "validating": (255, 255, 0),
    "granted": (0, 255, 0),
    "denied": (0, 0, 255),
    "error": (0, 0, 255),
}

# Estado visual sincronizado con la respuesta del Backend para el operario
gate_ui_banner = {
    "entry": {"text": "ESTADO: ESCANEANDO ENTRADA...", "color": COLOR_SCANNING, "until": 0},
    "exit": {"text": "ESTADO: ESCANEANDO SALIDA...", "color": COLOR_SCANNING, "until": 0}
}

# Tabla Gamma precalculada en memoria para no recrearla en cada frame nocturno
GAMMA_TABLE = np.array([((i / 255.0) ** (1.0 / 1.5)) * 255 for i in np.arange(0, 256)]).astype("uint8")

api = BackendClient(API_URL, DEVICE_API_KEY)
gates = GateController(ARDUINO_PORT, ARDUINO_BAUD)


def notify(gate_type: str, notice: Notice, plate: str | None) -> None:
    """Actualiza la ventana del operario y la pantalla pública del carril."""
    gate_ui_banner[gate_type] = {
        "text": notice.banner,
        "color": STATE_COLORS.get(notice.state, COLOR_SCANNING),
        "until": time.time() + notice.duration,
    }
    api.send_later("PUT", f"/devices/display/{gate_type}", {
        "state": notice.state,
        "message": notice.message,
        "plate": plate,
        "duration_seconds": notice.duration,
    })


flow = GateFlow(api, gates, notify)


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
        color = COLOR_SCANNING

    # Barra superior oscura para legibilidad
    cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], 50), (20, 20, 20), -1)
    cv2.putText(display_frame, text, (15, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)


def encode_snapshot(frame) -> str | None:
    height, width = frame.shape[:2]
    if width > SNAPSHOT_MAX_WIDTH:
        frame = cv2.resize(frame, (SNAPSHOT_MAX_WIDTH, int(height * SNAPSHOT_MAX_WIDTH / width)))
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return base64.b64encode(buffer.tobytes()).decode() if ok else None


def watch_unreadable_plate(frame, gate_type: str, current_time: float) -> None:
    """Hay placa a la vista pero sin consenso: se alerta al operador para resolverla a mano."""
    attempt = read_attempt[gate_type]
    if current_time - attempt["last"] > BUFFER_TIMEOUT:
        attempt["since"] = current_time
    attempt["last"] = current_time

    recently_read = current_time - last_seen_plates[gate_type]["time"] < COOLDOWN_SECONDS
    recently_alerted = current_time - last_unreadable_alert[gate_type] < UNREADABLE_COOLDOWN_SECONDS
    if recently_read or recently_alerted or current_time - attempt["since"] < UNREADABLE_AFTER_SECONDS:
        return

    last_unreadable_alert[gate_type] = current_time
    logger.warning(f"[{gate_type.upper()}] Placa no reconocida tras {UNREADABLE_AFTER_SECONDS:.0f} s")
    notify(gate_type, Notice("error", "PLACA NO RECONOCIDA - AVISANDO OPERADOR",
                             "No pudimos leer la placa. Un operador lo atenderá", duration=8.0), None)
    api.send_later("POST", "/interventions/alerts", {
        "gate": gate_type,
        "alert_type": "plate_unreadable",
        "message": "La cámara detectó una placa que no se pudo leer",
        "snapshot_b64": encode_snapshot(frame),
    })


def dispatch(gate_type: str, plate: str, vehicle_type) -> None:
    if gate_type == "entry":
        target, args = flow.process_entry, (plate, vehicle_type.value)
    else:
        target, args = flow.process_exit, (plate,)
    threading.Thread(target=target, args=args, daemon=True).start()


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
            current_time = time.time()
            watch_unreadable_plate(frame, gate_type, current_time)

            result = plate_reader.read_text(processed_plate)

            if result and result.license_plate:
                plate = result.license_plate

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

                        dispatch(gate_type, plate, result.vehicle_type)

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

    MAX_FAILED_READS = 50

    def __init__(self, src: int, name: str):
        self.src = src
        self.name = name
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_DSHOW)
        self.ret, self.frame = self.cap.read()
        self.failed_reads = 0
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
                self.failed_reads = 0
            else:
                self.ret = False
                self.failed_reads += 1
                # Una cámara USB desconectada sigue figurando como abierta
                if self.failed_reads >= self.MAX_FAILED_READS:
                    self.cap.release()
                    self.failed_reads = 0
                time.sleep(0.1)

    def read(self):
        return self.ret, self.frame

    def health(self) -> tuple[str, str | None]:
        if not self.cap.isOpened():
            return "no_communication", f"No se pudo abrir la cámara {self.name}"
        if not self.ret:
            return "error", f"La cámara {self.name} no entrega imagen"
        return "connected", None

    def release(self):
        self.running = False
        self.thread.join(timeout=1.0)
        if self.cap.isOpened():
            self.cap.release()


def gate_reports() -> list[dict]:
    gates.ensure_connected()
    if not gates.is_connected or not gates.ping():
        message = f"Sin comunicación con el Arduino en {ARDUINO_PORT}"
        return [
            {"code": code, "status": "no_communication", "error": message}
            for code in ("gate_entry", "gate_exit")
        ]

    reports = []
    for gate, code in (("entry", "gate_entry"), ("exit", "gate_exit")):
        failure = gates.last_failure[gate]
        reports.append({"code": code, "status": "error" if failure else "connected", "error": failure})
    return reports


def heartbeat_loop(cam_entry: CameraReader, cam_exit: CameraReader) -> None:
    applied_open_seconds = None

    while True:
        started = time.time()
        try:
            reports = gate_reports()
            for code, camera in (("camera_entry", cam_entry), ("camera_exit", cam_exit)):
                status, error = camera.health()
                reports.append({"code": code, "status": status, "error": error})

            response = api.post("/devices/heartbeat", {"devices": reports}, attempts=1)
            if response is not None and response.status_code == 200:
                data = response.json()

                seconds = data["gate_open_seconds"]
                if seconds != applied_open_seconds and gates.set_open_seconds(seconds):
                    applied_open_seconds = seconds
                    logger.info(f"Tiempo de apertura configurado en {seconds} s")
                if not gates.is_connected:
                    applied_open_seconds = None  # al reconectar, el Arduino vuelve a su valor inicial

                for command in data["commands"]:
                    flow.run_manual_command(command["id"], command["gate"])
            elif response is not None:
                logger.error(f"Heartbeat rechazado: HTTP {response.status_code}")
        except Exception:
            logger.exception("Falló el ciclo de heartbeat")

        time.sleep(max(0.0, HEARTBEAT_SECONDS - (time.time() - started)))


def process_streams(detection, plate_reader):
    logger.info(f"Iniciando monitoreo dual -> Entrada (Idx: {CAM_ENTRY_INDEX}) | Salida (Idx: {CAM_EXIT_INDEX})")

    cam_entry = CameraReader(CAM_ENTRY_INDEX, "Entrada")
    cam_exit = CameraReader(CAM_EXIT_INDEX, "Salida")
    threading.Thread(target=heartbeat_loop, args=(cam_entry, cam_exit), daemon=True).start()

    TARGET_FPS = 5
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
    if not DEVICE_API_KEY:
        logger.error("Falta DEVICE_API_KEY en el .env: sin ella el backend rechaza al worker")
        sys.exit(1)

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
        gates.close()
        sys.exit(0)
