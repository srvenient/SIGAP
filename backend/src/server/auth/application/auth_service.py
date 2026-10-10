from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID, uuid4

from jwt import InvalidTokenError
from pydantic import ValidationError

from core import security
from core.config import settings
from src.server.auth.domain.token.token import TokenPayload
from src.server.auth.domain.token.refresh_token import RefreshToken
from src.server.auth.domain.token.refresh_token_repository import RefreshTokenRepository
from src.server.auth.domain.exceptions import InvalidCredentials, AccountLocked, InactiveUser, InvalidToken, \
    InvalidPassword, SamePassword
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

    async def _user_from_token(self, token: str, aud: str) -> User:
        try:
            data = TokenPayload(**security.decode_token(token, aud))
        except (InvalidTokenError, ValidationError):
            raise InvalidToken from None

        user = await self.user_repository.find_by_id(data.sub)
        if user is None or not user.is_active:
            raise InvalidToken  # mismo error: no se filtra si el usuario existe

        # Tokens emitidos antes del último cambio de contraseña ya no valen
        if user.password_changed_at and data.iat < int(user.password_changed_at.timestamp()):
            raise InvalidToken

        return user

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

    async def get_user_from_token(self, access_token: str) -> User:
        return await self._user_from_token(access_token, security.ACCESS_AUD)

    async def refresh(self, raw_refresh_token: str) -> LoginResult:
        stored = await self.refresh_token_repository.find_by_hash(
            security.hash_refresh_token(raw_refresh_token)
        )
        if stored is None:
            raise InvalidToken

        now = get_localized_now()
        if stored.expires_at <= now:
            raise InvalidToken

        if stored.revoked_at is not None:
            grace = timedelta(seconds=settings.REFRESH_REUSE_GRACE_SECONDS)
            if now - stored.revoked_at > grace:
                # Un token ya usado reapareció: hay dos copias en circulación.
                # Se revoca toda la familia (el atacante y el usuario legítimo deben iniciar sesión).
                await self.refresh_token_repository.revoke_family(stored.family_id)
                raise InvalidToken
            # Dentro de la gracia: carrera legítima (p. ej. dos pestañas), se continúa

        user = await self.user_repository.find_by_id(stored.user_id)
        if user is None or not user.is_active:
            await self.refresh_token_repository.revoke_family(stored.family_id)
            raise InvalidToken

        if stored.revoked_at is None:
            await self.refresh_token_repository.revoke(stored.id)

        access, refresh = await self._issue_session(user, family_id=stored.family_id)
        return LoginResult(user, access_token=access, refresh_token=refresh)

    async def logout(self, raw_refresh_token: str) -> None:
        stored = await self.refresh_token_repository.find_by_hash(
            security.hash_refresh_token(raw_refresh_token)
        )
        if stored is not None:
            await self.refresh_token_repository.revoke_family(stored.family_id)

    async def logout_all(self, user: User) -> None:
        await self.refresh_token_repository.revoke_all_for_user(user.id)

    async def change_password(
            self, user: User, current_password: str, new_password: str
    ) -> tuple[str, str]:
        if not security.verify_password(current_password, user.hashed_password):
            raise InvalidPassword
        if security.verify_password(new_password, user.hashed_password):
            raise SamePassword

        user.hashed_password = security.get_password_hash(new_password)
        user.must_change_password = False
        user.password_changed_at = get_localized_now()
        await self.user_repository.save(user)

        await self.refresh_token_repository.revoke_all_for_user(user.id)
        return await self._issue_session(user)
