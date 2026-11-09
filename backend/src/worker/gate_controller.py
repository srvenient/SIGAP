import threading
import time
from typing import Any, Callable

import serial
from loguru import logger

COMMAND_BY_GATE = {"entry": "E", "exit": "S"}


class GateController:
    """Habla con el Arduino. El lock garantiza una orden a la vez sobre el puerto serial."""

    def __init__(
            self,
            port: str,
            baud: int,
            ack_timeout: float = 1.5,
            reset_delay: float = 2.0,
            serial_factory: Callable[..., Any] = serial.Serial,
    ):
        self.port = port
        self.baud = baud
        self.ack_timeout = ack_timeout
        self.reset_delay = reset_delay
        self.serial_factory = serial_factory
        self.last_failure: dict[str, str | None] = {"entry": None, "exit": None}
        self._connection: Any = None
        self._lock = threading.Lock()

    @property
    def is_connected(self) -> bool:
        return self._connection is not None

    def ensure_connected(self) -> bool:
        with self._lock:
            if self._connection is not None:
                return True
            try:
                connection = self.serial_factory(self.port, self.baud, timeout=0.1)
                time.sleep(self.reset_delay)  # abrir el puerto reinicia el Arduino
                self._connection = connection
                logger.success(f"Arduino conectado en {self.port}")
                return True
            except Exception as exc:
                logger.warning(f"Arduino no disponible en {self.port}: {exc}")
                return False

    def _drop_connection(self, reason: Exception) -> None:
        logger.error(f"Se perdió la conexión con el Arduino: {reason}")
        try:
            self._connection.close()
        except Exception:
            pass
        self._connection = None

    def _exchange(self, command: bytes, expected: str) -> bool:
        """Envía la orden y espera `expected`; descarta avisos como CLOSED:E que lleguen antes."""
        with self._lock:
            if self._connection is None:
                return False
            try:
                self._connection.reset_input_buffer()
                self._connection.write(command)
                deadline = time.monotonic() + self.ack_timeout
                while time.monotonic() < deadline:
                    line = self._connection.readline().decode("ascii", errors="ignore").strip()
                    if line == expected:
                        return True
                return False
            except Exception as exc:
                self._drop_connection(exc)
                return False

    def open(self, gate: str) -> bool:
        code = COMMAND_BY_GATE[gate]
        acknowledged = self._exchange(code.encode(), f"ACK:{code}")
        if acknowledged:
            logger.info(f"Talanquera {gate} abierta (ACK:{code})")
            self.last_failure[gate] = None
        else:
            self.last_failure[gate] = "La talanquera no confirmó la orden de apertura"
            logger.error(f"Sin confirmación del Arduino para la talanquera {gate}")
        return acknowledged

    def ping(self) -> bool:
        return self._exchange(b"P", "PONG")

    def set_open_seconds(self, seconds: int) -> bool:
        return self._exchange(f"T{seconds}\n".encode(), f"OK:T={seconds}")

    def close(self) -> None:
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None
