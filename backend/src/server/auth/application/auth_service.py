from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID, uuid4

from core import security
from core.config import settings
from src.server.auth.domain.token.refresh_token import RefreshToken
from src.server.auth.domain.token.refresh_token_repository import RefreshTokenRepository
from src.server.auth.domain.exceptions import InvalidCredentials, AccountLocked, InactiveUser
from src.server.auth.domain.user.user import User
from src.server.auth.domain.user.user_repository import UserRepository
from src.server.shared.infrastructure.providers.system_clock import get_localized_now


@dataclass(frozen=True)
class LoginResult:
    user: User
    access_token: str | None = None
    refresh_token: str | None = None


class AuthService:
    def __init__(self, user_repository: UserRepository, refresh_token_repository: RefreshTokenRepository):
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository

    @staticmethod
    def _is_locked(user: User) -> bool:
        return user.locked_until is not None and user.locked_until > get_localized_now()

    @staticmethod
    def _seconds_left(user: User) -> int:
        return max(1, int((user.locked_until - get_localized_now()).total_seconds()))  # type: ignore[operator]

    async def _register_failure(self, user: User) -> None:
        attempts = user.failed_login_attempts + 1
        if attempts >= settings.FAILED_LOGIN_ATTEMPTS:
            changes = {
                "failed_login_attempts": 0,
                "locked_until": get_localized_now() + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES),
            }
        else:
            changes = {"failed_login_attempts": attempts}
        await self.user_repository.update(user.id, changes)

    async def _issue_session(self, user: User, family_id: UUID | None = None) -> tuple[str, str]:
        access = security.create_access_token(user.id)
        raw, hashed = security.generate_refresh_token()
        await self.refresh_token_repository.save(RefreshToken(
            user_id=user.id,
            family_id=family_id or uuid4(),
            token_hash=hashed,
            expires_at=get_localized_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ))
        return access, raw

    async def _complete_login(self, user: User) -> LoginResult:
        await self.user_repository.update(
            user.id,
            {"last_login": get_localized_now(), "failed_login_attempts": 0, "locked_until": None},
        )
        access, refresh = await self._issue_session(user)
        return LoginResult(user, access_token=access, refresh_token=refresh)

    async def authenticate(self, username: str, password: str):
        user: User | None = await self.user_repository.find_by_username(username)

        # Siempre se verifica un hash, exista o no el usuario (anti timing attack)
        hashed = user.hashed_password if user else security.DUMMY_HASHED_PASSWORD
        password_ok = security.verify_password(password, hashed)

        if user is None:
            raise InvalidCredentials

        # Cuenta bloqueada: no se evalúa la contraseña (si no, el atacante seguiría
        # recibiendo información durante el bloqueo)
        if self._is_locked(user):
            raise AccountLocked(self._seconds_left(user))

        if not password_ok:
            await self._register_failure(user)
            raise InvalidCredentials

        # Después de validar la contraseña: no revela qué cuentas están inactivas
        if not user.is_active:
            raise InactiveUser

        return await self._complete_login(user)
