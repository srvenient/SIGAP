from typing import Annotated

from fastapi import Depends

from src.server.auth.application.auth_service import AuthService
from src.server.auth.application.user_service import UserService
from src.server.auth.domain.role.role_repository import RoleRepository
from src.server.auth.domain.user.user_repository import UserRepository
from src.server.auth.domain.token.refresh_token_repository import RefreshTokenRepository
from src.server.auth.infrastructure.postgres_refresh_token_repository import PostgresRefreshTokenRepository
from src.server.auth.infrastructure.postgres_role_repository import PostgresRoleRepository
from src.server.auth.infrastructure.postgres_user_repository import PostgresUserRepository
from src.server.shared.api.deps import SessionDep


def get_role_repository(session: SessionDep) -> RoleRepository:
    return PostgresRoleRepository(session=session)


def get_user_repository(session: SessionDep) -> UserRepository:
    return PostgresUserRepository(session=session)


def get_refresh_token_repository(session: SessionDep) -> RefreshTokenRepository:
    return PostgresRefreshTokenRepository(session=session)


RoleRepositoryDep = Annotated[RoleRepository, Depends(get_role_repository)]
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
RefreshTokenRepositoryDep = Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)]


def get_user_service(
        user_repository: UserRepositoryDep,
        role_repository: RoleRepositoryDep,
        refresh_token_repository: RefreshTokenRepositoryDep
) -> UserService:
    return UserService(
        user_repository=user_repository,
        role_repository=role_repository,
        refresh_token_repository=refresh_token_repository
    )


def get_auth_service(
        user_repository: UserRepositoryDep,
        refresh_token_repository: RefreshTokenRepositoryDep
) -> AuthService:
    return AuthService(user_repository=user_repository, refresh_token_repository=refresh_token_repository)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
