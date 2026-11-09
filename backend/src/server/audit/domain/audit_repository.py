from abc import ABC, abstractmethod
from datetime import datetime
from typing import Literal

from src.server.audit.domain.audit_log import AuditAction, AuditLog


class AuditRepository(ABC):
    """Solo agrega y consulta: a propósito no existen update ni delete (HU-28)."""

    @abstractmethod
    def add(self, entry: AuditLog) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def search(
            self,
            action: AuditAction | None,
            username: str | None,
            start: datetime | None,
            end: datetime | None,
            order: Literal["asc", "desc"],
            skip: int,
            limit: int,
    ) -> tuple[list[AuditLog], int]: ...
