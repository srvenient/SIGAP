from abc import ABC, abstractmethod
from uuid import UUID

from src.server.device.domain.device import Gate
from src.server.intervention.domain.alert import (
    AlertSnapshot,
    AlertStatus,
    AlertType,
    OperationAlert,
)


class AlertRepository(ABC):
    @abstractmethod
    async def find_by_id(self, alert_id: UUID, for_update: bool = False) -> OperationAlert | None: ...

    @abstractmethod
    async def find_pending_duplicate(
            self, alert_type: AlertType, gate: Gate, plate: str | None
    ) -> OperationAlert | None: ...

    @abstractmethod
    async def search(self, status: AlertStatus | None, limit: int) -> list[OperationAlert]: ...

    @abstractmethod
    async def get_snapshot(self, alert_id: UUID) -> AlertSnapshot | None: ...

    @abstractmethod
    async def delete_snapshot(self, alert_id: UUID) -> None: ...

    @abstractmethod
    def add(self, entity: OperationAlert | AlertSnapshot) -> None: ...

    @abstractmethod
    async def flush(self) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...
