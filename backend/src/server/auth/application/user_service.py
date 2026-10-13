import secrets
from uuid import UUID

from core import security
from src.server.shared.infrastructure.providers.system_clock import get_localized_now
from src.server.auth.domain.exceptions import UsernameAlreadyExists, RoleNotFound, CannotModifySelf, UserNotFound, \
    LastActiveAdmin
from src.server.auth.domain.role.role import RoleName
from src.server.auth.domain.user.user import User, UserCreate, UserUpdate
from src.server.auth.domain.user.user_repository import UserRepository
from src.server.auth.domain.role.role_repository import RoleRepository
from src.server.auth.domain.token.refresh_token_repository import RefreshTokenRepository


class UserService:
    def __init__(
            self,
            user_repository: UserRepository,
            role_repository: RoleRepository,
            refresh_token_repository: RefreshTokenRepository
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.refresh_token_repository = refresh_token_repository

    async def create_user(self, user_create: UserCreate, must_change_password: bool = True) -> User:
        if await self.user_repository.find_by_username(user_create.username):
            raise UsernameAlreadyExists

        if not await self.role_repository.find_by_id(user_create.role_id):
            raise RoleNotFound

        user = User(
            username=user_create.username,
            hashed_password=security.get_password_hash(user_create.password),
            role_id=user_create.role_id,
            is_active=user_create.is_active,
            must_change_password=must_change_password,
        )

        return await self.user_repository.save(user)

    async def list_users(self, skip: int = 0, limit: int = 50) -> tuple[list[User], int]:
        users = await self.user_repository.find_all(skip=skip, limit=limit)
        return users, await self.user_repository.count()

    async def get_user(self, user_id: UUID) -> User:
        user = await self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFound
        return user

    async def update_user(self, actor: User, user_id: UUID, data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        changes = data.model_dump(exclude_none=True)

        # Evita que el admin se bloquee a sí mismo (desactivarse o quitarse el rol)
        if actor.id == user.id and (
                changes.get("is_active") is False
                or ("role_id" in changes and changes["role_id"] != user.role_id)
        ):
            raise CannotModifySelf

        if "role_id" in changes and not await self.role_repository.find_by_id(changes["role_id"]):
            raise RoleNotFound

        # Evita dejar el sistema sin administradores activos
        loses_admin = (
            user.is_active
            and user.role is not None
            and user.role.name == RoleName.ADMIN.value
            and (
                changes.get("is_active") is False
                or ("role_id" in changes and changes["role_id"] != user.role_id)
            )
        )
        if loses_admin and await self.user_repository.count_active_by_role(user.role_id) <= 1:  # type: ignore[arg-type]
            raise LastActiveAdmin

        updated = await self.user_repository.update(user_id, changes)

        if changes.get("is_active") is False:
            # Desactivar cierra todas sus sesiones (el access token ya falla por is_active)
            await self.refresh_token_repository.revoke_all_for_user(user_id)

        return updated  # type: ignore[return-value]

    async def reset_password(self, actor: User, user_id: UUID) -> str:
        """Genera una contraseña temporal. Se devuelve una sola vez al admin."""
        user = await self.get_user(user_id)
        if actor.id == user.id:
            raise CannotModifySelf  # el admin usa /auth/change-password para la suya

        temporary = secrets.token_urlsafe(9)
        user.hashed_password = security.get_password_hash(temporary)
        user.must_change_password = True
        user.password_changed_at = get_localized_now()  # invalida los access tokens activos
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.user_repository.save(user)
        await self.refresh_token_repository.revoke_all_for_user(user_id)  # y los refresh
        return temporary

    async def unlock_user(self, user_id: UUID) -> None:
        await self.get_user(user_id)
        await self.user_repository.update(
            user_id, {"failed_login_attempts": 0, "locked_until": None}
        )
