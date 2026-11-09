from typing import Any

from src.server.audit.domain.audit_log import Actor, AuditAction, AuditLog, AuditResult
from src.server.audit.domain.audit_repository import AuditRepository


class AuditRecorder:
    """Agrega el registro a la sesión actual, sin confirmar.

    Se debe llamar antes del `save`/`update` de la acción auditada: ambos quedan en el mismo
    commit, así que no puede existir una acción sin su registro. Si no hay un guardado
    posterior (por ejemplo, un login fallido de un usuario inexistente), usar `flush`.
    """

    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def record(
            self,
            action: AuditAction,
            actor: Actor,
            entity_type: str,
            entity_id: Any = None,
            entity_label: str | None = None,
            result: AuditResult = AuditResult.SUCCESS,
            detail: dict[str, Any] | None = None,
    ) -> None:
        self.repository.add(AuditLog(
            actor_user_id=actor.user_id,
            actor_label=actor.label,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            entity_label=entity_label,
            result=result,
            detail=detail or {},
        ))

    async def flush(self) -> None:
        await self.repository.commit()
