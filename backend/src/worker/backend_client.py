import queue
import threading
import time
from typing import Any

import requests
from loguru import logger

_RETRY_DELAY_SECONDS = 1.0


class BackendClient:
    """Cliente HTTP del worker. Reintenta ante fallos de red o errores 5xx."""

    def __init__(self, base_url: str, device_key: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-Device-Key": device_key}
        self.timeout = timeout
        self._background: queue.Queue[tuple[str, str, Any]] = queue.Queue(maxsize=50)
        threading.Thread(target=self._drain_background, daemon=True).start()

    def request(
            self, method: str, path: str, payload: Any = None, attempts: int = 3
    ) -> requests.Response | None:
        """Devuelve la respuesta, o None si el servidor no pudo responderla."""
        for attempt in range(1, attempts + 1):
            try:
                response = requests.request(
                    method, f"{self.base_url}{path}", json=payload, headers=self.headers, timeout=self.timeout
                )
                if response.status_code < 500:
                    return response
                logger.warning(f"{method} {path}: HTTP {response.status_code} (intento {attempt}/{attempts})")
            except requests.exceptions.RequestException as exc:
                logger.warning(f"{method} {path}: {exc} (intento {attempt}/{attempts})")
            if attempt < attempts:
                time.sleep(_RETRY_DELAY_SECONDS)
        return None

    def post(self, path: str, payload: Any = None, attempts: int = 3) -> requests.Response | None:
        return self.request("POST", path, payload, attempts)

    def send_later(self, method: str, path: str, payload: Any) -> None:
        """Para avisos que no deben frenar el procesamiento de video. Si la cola está llena, se descarta."""
        try:
            self._background.put_nowait((method, path, payload))
        except queue.Full:
            logger.warning(f"Cola de avisos llena; se descarta {method} {path}")

    def _drain_background(self) -> None:
        while True:
            method, path, payload = self._background.get()
            self.request(method, path, payload, attempts=1)
