from typing import Annotated

from fastapi import Depends

from src.server.shared.api.deps import SessionDep
from src.server.auth.domain.role.role_repository import RoleRepository
from src.server.auth.infrastructure.postgres_role_repository import PostgresRoleRepository
from src.server.auth.domain.user.user_repository import UserRepository
from src.server.auth.application.user_service import UserService
from src.server.auth.infrastructure.postgres_user_repository import PostgresUserRepository


def get_role_repository(session: SessionDep) -> RoleRepository:
    return PostgresRoleRepository(session=session)


def get_user_repository(session: SessionDep) -> UserRepository:
    return PostgresUserRepository(session=session)


RoleRepositoryDep = Annotated[RoleRepository, Depends(get_role_repository)]
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_user_service(
        user_repository: UserRepositoryDep,
        role_repository: RoleRepositoryDep
) -> UserService:
    return UserService(user_repository=user_repository, role_repository=role_repository)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
