from typing import Annotated

from fastapi import Depends

from src.server.intervention.application.intervention_service import InterventionService
from src.server.shared.api.deps import SessionDep
from src.server.wiring import build_intervention_service


def get_intervention_service(session: SessionDep) -> InterventionService:
    return build_intervention_service(session)


InterventionServiceDep = Annotated[InterventionService, Depends(get_intervention_service)]
