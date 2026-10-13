from uuid import UUID

from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from src.server.auth.api.deps import AdminUserDep, UserServiceDep, RoleRepositoryDep
from src.server.auth.domain.role.role import RolePublic, RolesPublic
from src.server.auth.domain.user.user import UserCreate, UserPublic, UsersPublic, UserUpdate

# Todas las rutas de este router requieren sesión válida + rol admin.
user_router = APIRouter(prefix="/users", tags=["users"])


class TemporaryPassword(BaseModel):
    temporary_password: str


@user_router.get("/roles", response_model=RolesPublic)
async def list_roles(_: AdminUserDep, role_repository: RoleRepositoryDep):
    """Roles disponibles para asignar (declarada antes de /{user_id})."""
    roles = await role_repository.find_all()
    return RolesPublic(roles=[RolePublic.model_validate(r) for r in roles], count=len(roles))


@user_router.get("", response_model=UsersPublic)
async def list_users(
        _: AdminUserDep,
        user_service: UserServiceDep,
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
):
    users, count = await user_service.list_users(skip=skip, limit=limit)
    return UsersPublic(data=[UserPublic.model_validate(u) for u in users], count=count)


@user_router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreate, _: AdminUserDep, user_service: UserServiceDep):
    return await user_service.create_user(body)


@user_router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: UUID, _: AdminUserDep, user_service: UserServiceDep):
    return await user_service.get_user(user_id)


@user_router.patch("/{user_id}", response_model=UserPublic)
async def update_user(user_id: UUID, body: UserUpdate, admin: AdminUserDep, user_service: UserServiceDep):
    return await user_service.update_user(admin, user_id, body)


@user_router.post("/{user_id}/reset-password", response_model=TemporaryPassword)
async def reset_password(user_id: UUID, admin: AdminUserDep, user_service: UserServiceDep):
    """Devuelve la contraseña temporal UNA sola vez; no se almacena en claro."""
    temporary = await user_service.reset_password(admin, user_id)
    return TemporaryPassword(temporary_password=temporary)


@user_router.post("/{user_id}/unlock", status_code=status.HTTP_204_NO_CONTENT)
async def unlock_user(user_id: UUID, _: AdminUserDep, user_service: UserServiceDep):
    await user_service.unlock_user(user_id)
