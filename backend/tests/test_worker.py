from dataclasses import dataclass, field
from typing import Any

import pytest
import serial

from src.worker.gate_controller import GateController
from src.worker.gate_flow import GateFlow


class FakeArduino:
    """Responde como el sketch; `silent` simula un Arduino colgado."""

    def __init__(self, silent: bool = False, fail_on_write: bool = False):
        self.silent = silent
        self.fail_on_write = fail_on_write
        self.written: list[bytes] = []
        self.lines: list[bytes] = []
        self.closed = False

    def reset_input_buffer(self) -> None:
        self.lines.clear()

    def write(self, data: bytes) -> None:
        if self.fail_on_write:
            raise serial.SerialException("desconectado")
        self.written.append(data)
        if self.silent:
            return
        if data in (b"E", b"S"):
            self.lines += [b"CLOSED:X\r\n", b"ACK:" + data + b"\r\n"]
        elif data == b"P":
            self.lines.append(b"PONG\r\n")
        elif data.startswith(b"T"):
            self.lines.append(b"OK:T=" + data[1:].strip() + b"\r\n")

    def readline(self) -> bytes:
        return self.lines.pop(0) if self.lines else b""

    def close(self) -> None:
        self.closed = True


def controller(device: FakeArduino) -> GateController:
    gates = GateController("COM9", 9600, ack_timeout=0.05, reset_delay=0, serial_factory=lambda *a, **k: device)
    assert gates.ensure_connected()
    return gates


@pytest.mark.parametrize(("gate", "command"), [("entry", b"E"), ("exit", b"S")])
def test_open_waits_for_ack_skipping_other_lines(gate: str, command: bytes) -> None:
    device = FakeArduino()

    assert controller(device).open(gate) is True
    assert device.written == [command]


def test_open_without_ack_reports_failure() -> None:
    gates = controller(FakeArduino(silent=True))

    assert gates.open("entry") is False
    assert gates.last_failure["entry"] is not None


def test_successful_open_clears_previous_failure() -> None:
    device = FakeArduino(silent=True)
    gates = controller(device)
    gates.open("entry")

    device.silent = False

    assert gates.open("entry") is True
    assert gates.last_failure["entry"] is None


def test_ping_and_open_seconds() -> None:
    device = FakeArduino()
    gates = controller(device)

    assert gates.ping() is True
    assert gates.set_open_seconds(7) is True
    assert device.written[-1] == b"T7\n"


def test_lost_connection_is_dropped_and_recovers() -> None:
    broken = FakeArduino(fail_on_write=True)
    healthy = FakeArduino()
    devices = iter([broken, healthy])
    gates = GateController("COM9", 9600, ack_timeout=0.05, reset_delay=0, serial_factory=lambda *a, **k: next(devices))
    gates.ensure_connected()

    assert gates.open("exit") is False
    assert gates.is_connected is False
    assert broken.closed is True

    assert gates.ensure_connected() is True
    assert gates.open("exit") is True


def test_unavailable_port_does_not_raise() -> None:
    def fail(*_: Any, **__: Any):
        raise serial.SerialException("puerto ocupado")

    gates = GateController("COM9", 9600, reset_delay=0, serial_factory=fail)

    assert gates.ensure_connected() is False
    assert gates.open("entry") is False


@dataclass
class FakeResponse:
    status_code: int
    body: dict = field(default_factory=dict)

    def json(self) -> dict:
        return self.body


class FakeApi:
    def __init__(self, responses: dict[str, FakeResponse | None]):
        self.responses = responses
        self.calls: list[tuple[str, Any]] = []

    def post(self, path: str, payload: Any = None, attempts: int = 3):
        self.calls.append((path, payload))
        for fragment, response in self.responses.items():
            if fragment in path:
                return response
        return FakeResponse(200, {})

    @property
    def paths(self) -> list[str]:
        return [path for path, _ in self.calls]


def flow(api: FakeApi, device: FakeArduino) -> tuple[GateFlow, list]:
    notices: list = []
    return GateFlow(api, controller(device), lambda g, n, p: notices.append(n)), notices  # type: ignore[arg-type]


def test_entry_opens_only_after_transaction_is_created() -> None:
    api = FakeApi({"/transactions/entry": FakeResponse(201, {"id": "tx1"})})
    device = FakeArduino()
    gate_flow, notices = flow(api, device)

    assert gate_flow.process_entry("ABC123", "car") is True
    assert device.written == [b"E"]
    assert api.paths == ["/transactions/entry", "/transactions/tx1/entry-gate-opened"]
    assert notices[-1].state == "granted"


@pytest.mark.parametrize(("status", "expected"), [(400, "ingreso"), (409, "lleno"), (422, "válida")])
def test_rejected_entry_never_opens(status: int, expected: str) -> None:
    device = FakeArduino()
    gate_flow, notices = flow(FakeApi({"/transactions/entry": FakeResponse(status)}), device)

    assert gate_flow.process_entry("ABC123", "car") is False
    assert device.written == []
    assert expected in notices[-1].message


def test_entry_without_server_never_opens() -> None:
    device = FakeArduino()
    gate_flow, notices = flow(FakeApi({"/transactions/entry": None}), device)

    assert gate_flow.process_entry("ABC123", "car") is False
    assert device.written == []
    assert notices[-1].state == "error"


def test_entry_gate_failure_reports_and_does_not_confirm() -> None:
    api = FakeApi({"/transactions/entry": FakeResponse(201, {"id": "tx1"})})
    gate_flow, notices = flow(api, FakeArduino(silent=True))

    assert gate_flow.process_entry("ABC123", "car") is False
    assert "/transactions/tx1/entry-gate-opened" not in api.paths
    assert "/devices/events" in api.paths
    event = dict(api.calls)["/devices/events"]
    assert event["device_code"] == "gate_entry"
    assert event["transaction_id"] == "tx1"
    assert notices[-1].state == "error"


def test_exit_completes_only_after_ack() -> None:
    api = FakeApi({"/authorize": FakeResponse(200, {"id": "tx1"})})
    device = FakeArduino()
    gate_flow, _ = flow(api, device)

    assert gate_flow.process_exit("ABC123") is True
    assert device.written == [b"S"]
    assert api.paths == ["/transactions/exit/ABC123/authorize", "/transactions/tx1/exit-confirm"]


def test_exit_without_ack_does_not_finalize() -> None:
    api = FakeApi({"/authorize": FakeResponse(200, {"id": "tx1"})})
    gate_flow, _ = flow(api, FakeArduino(silent=True))

    assert gate_flow.process_exit("ABC123") is False
    assert "/transactions/tx1/exit-confirm" not in api.paths
    assert dict(api.calls)["/devices/events"]["device_code"] == "gate_exit"


@pytest.mark.parametrize(("status", "expected"), [(402, "Pago pendiente"), (404, "No encontramos")])
def test_unauthorized_exit_never_opens(status: int, expected: str) -> None:
    device = FakeArduino()
    gate_flow, notices = flow(FakeApi({"/authorize": FakeResponse(status)}), device)

    assert gate_flow.process_exit("ABC123") is False
    assert device.written == []
    assert expected in notices[-1].message


@pytest.mark.parametrize(("silent", "success"), [(False, True), (True, False)])
def test_manual_command_reports_result(silent: bool, success: bool) -> None:
    api = FakeApi({})
    gate_flow, _ = flow(api, FakeArduino(silent=silent))

    assert gate_flow.run_manual_command("cmd1", "exit") is success
    assert dict(api.calls)["/devices/commands/cmd1/result"]["success"] is success
