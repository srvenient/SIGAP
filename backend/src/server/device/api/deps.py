from typing import Annotated

from fastapi import Depends

from src.server.device.application.device_service import DeviceService
from src.server.shared.api.deps import SessionDep
from src.server.wiring import build_device_service


def get_device_service(session: SessionDep) -> DeviceService:
    return build_device_service(session)


DeviceServiceDep = Annotated[DeviceService, Depends(get_device_service)]
