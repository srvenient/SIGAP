from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from src.server.audit.domain.audit_log import AuditAction, AuditLogPublic, AuditLogsPublic
from src.server.audit.domain.audit_repository import AuditRepository
from src.server.auth.api.deps import AdminUserDep
from src.server.shared.api.deps import SessionDep
from src.server.shared.application.date_range import day_bounds
from src.server.wiring import build_audit_repository


def _repository(session: SessionDep) -> AuditRepository:
    return build_audit_repository(session)


RepositoryDep = Annotated[AuditRepository, Depends(_repository)]

# Solo lectura: esta API no expone creación, edición ni borrado (HU-28).
audit_router = APIRouter(prefix="/audit", tags=["Audit"])


@audit_router.get("/actions", response_model=list[str])
async def list_actions(_: AdminUserDep):
    return [a.value for a in AuditAction]


@audit_router.get("", response_model=AuditLogsPublic)
async def list_audit_logs(
        _: AdminUserDep,
        repository: RepositoryDep,
        action: AuditAction | None = None,
        username: str | None = Query(default=None, max_length=80),
        date_from: date | None = None,
        date_to: date | None = None,
        order: Literal["asc", "desc"] = "desc",
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
):
    start, end = day_bounds(date_from, date_to)
    rows, count = await repository.search(action, username, start, end, order, skip, limit)
    return AuditLogsPublic(data=[AuditLogPublic.model_validate(r) for r in rows], count=count)
