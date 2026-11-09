from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.server.device.domain.device import (
    Device,
    Gate,
    GateCommand,
    GateDisplay,
    TechnicalEvent,
)


class DeviceRepository(ABC):
    @abstractmethod
    async def list_devices(self, parking_lot_id: UUID) -> list[Device]: ...

    @abstractmethod
    async def lock_devices(self, parking_lot_id: UUID) -> list[Device]: ...

    @abstractmethod
    async def lock_stale(self, cutoff: datetime) -> list[Device]:
        """Dispositivos sin reporte reciente. Salta los bloqueados por otro proceso."""

    @abstractmethod
    def add(self, entity: Device | GateCommand | GateDisplay | TechnicalEvent) -> None: ...

    @abstractmethod
    async def flush(self) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def list_events(self, skip: int, limit: int) -> tuple[list[TechnicalEvent], int]: ...

    @abstractmethod
    async def find_command(self, command_id: UUID) -> GateCommand | None: ...

    @abstractmethod
    async def lock_open_commands(self, parking_lot_id: UUID) -> list[GateCommand]: ...

    @abstractmethod
    async def recent_commands(self, limit: int) -> list[GateCommand]: ...

    @abstractmethod
    async def find_display(self, parking_lot_id: UUID, gate: Gate) -> GateDisplay | None: ...
