from abc import ABC, abstractmethod
from datetime import datetime

from src.server.reporting.domain.report import Revenue


class ReportRepository(ABC):
    @abstractmethod
    async def revenue(self, start: datetime | None, end: datetime | None) -> Revenue: ...

    @abstractmethod
    async def count_entries(self, start: datetime, end: datetime) -> int: ...

    @abstractmethod
    async def count_exits(self, start: datetime, end: datetime) -> int: ...
