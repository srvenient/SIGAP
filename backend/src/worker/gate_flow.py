from dataclasses import dataclass
from typing import Callable

from loguru import logger

from src.worker.backend_client import BackendClient
from src.worker.gate_controller import GateController

GATE_DEVICE = {"entry": "gate_entry", "exit": "gate_exit"}


@dataclass(frozen=True)
class Notice:
    """`banner` va a la ventana OpenCV (sin tildes: putText no las dibuja); `message`, al conductor."""

    state: str
    banner: str
    message: str
    duration: float = 7.0


NO_CONNECTION = Notice("error", "ERROR DE CONEXION CON SERVIDOR", "Sistema sin conexión. Un operador lo atenderá")
GATE_FAILED = Notice("error", "ERROR: TALANQUERA SIN RESPUESTA", "No pudimos abrir la talanquera. Un operador lo atenderá")

_ENTRY_REJECTIONS = {
    400: Notice("denied", "DENEGADO: {plate} YA ESTA ADENTRO", "Este vehículo ya registra un ingreso"),
    409: Notice("denied", "PARQUEADERO LLENO", "Parqueadero lleno: no hay cupos disponibles"),
    422: Notice("denied", "PLACA INVALIDA: {plate}", "La placa no es válida. Un operador lo atenderá"),
}
_EXIT_REJECTIONS = {
    402: Notice("denied", "DENEGADO: PAGO PENDIENTE ({plate})", "Pago pendiente. Diríjase al módulo de pago"),
    404: Notice("denied", "DENEGADO: SIN ENTRADA ({plate})", "No encontramos su ingreso. Un operador lo atenderá"),
}

NotifyFn = Callable[[str, Notice, str | None], None]


class GateFlow:
    """Secuencia de negocio de cada carril: la talanquera solo abre con la autorización del backend."""

    def __init__(self, api: BackendClient, gates: GateController, notify: NotifyFn):
        self.api = api
        self.gates = gates
        self.notify = notify

    def _validating(self, gate: str, plate: str) -> None:
        self.notify(
            gate,
            Notice("validating", f"VALIDANDO EN SERVIDOR: {plate}...", "Validando placa", duration=5.0),
            plate,
        )

    def _reject(self, gate: str, plate: str, status: int, table: dict[int, Notice]) -> bool:
        notice = table.get(status) or Notice("error", f"ERROR ({status}): {{plate}}", "Un operador lo atenderá")
        self.notify(gate, Notice(notice.state, notice.banner.format(plate=plate), notice.message), plate)
        logger.warning(f"[{gate.upper()}] Rechazo {status} para {plate}")
        return False

    def _report_gate_failure(self, gate: str, plate: str, transaction_id: str) -> None:
        self.api.post("/devices/events", {
            "device_code": GATE_DEVICE[gate],
            "error_code": "GATE_NO_RESPONSE",
            "description": f"La talanquera no confirmó la apertura para la placa {plate}.",
            "transaction_id": transaction_id,
        })
        self.notify(gate, GATE_FAILED, plate)

    def process_entry(self, plate: str, vehicle_type: str) -> bool:
        self._validating("entry", plate)
        response = self.api.post("/transactions/entry", {"plate": plate, "vehicle_type": vehicle_type})
        if response is None:
            self.notify("entry", NO_CONNECTION, plate)
            return False
        if response.status_code not in (200, 201):
            return self._reject("entry", plate, response.status_code, _ENTRY_REJECTIONS)

        transaction_id = response.json()["id"]
        if not self.gates.open("entry"):
            self._report_gate_failure("entry", plate, transaction_id)
            return False

        self.api.post(f"/transactions/{transaction_id}/entry-gate-opened")
        self.notify("entry", Notice("granted", f"AUTORIZADO: {plate} - ABRIENDO", "Bienvenido, puede ingresar"), plate)
        return True

    def process_exit(self, plate: str) -> bool:
        self._validating("exit", plate)
        response = self.api.post(f"/transactions/exit/{plate}/authorize")
        if response is None:
            self.notify("exit", NO_CONNECTION, plate)
            return False
        if response.status_code != 200:
            return self._reject("exit", plate, response.status_code, _EXIT_REJECTIONS)

        transaction_id = response.json()["id"]
        if not self.gates.open("exit"):
            self._report_gate_failure("exit", plate, transaction_id)
            return False

        # La barrera ya abrió: si esto falla, hay que saberlo porque la transacción sigue Pagada
        confirmed = self.api.post(f"/transactions/{transaction_id}/exit-confirm")
        if confirmed is None or confirmed.status_code != 200:
            logger.error(f"[EXIT] La talanquera abrió pero no se pudo finalizar {transaction_id} ({plate})")
        self.notify("exit", Notice("granted", f"AUTORIZADO: {plate} - ABRIENDO", "Buen viaje, puede salir"), plate)
        return True

    def run_manual_command(self, command_id: str, gate: str) -> bool:
        opened = self.gates.open(gate)
        self.api.post(f"/devices/commands/{command_id}/result", {
            "success": opened,
            "error": None if opened else "La talanquera no confirmó la orden de apertura",
        })
        if opened:
            self.notify(gate, Notice("granted", "APERTURA MANUAL - ABRIENDO", "Puede continuar"), None)
        else:
            self.notify(gate, GATE_FAILED, None)
        return opened
