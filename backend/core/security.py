import hashlib
import secrets
from datetime import timedelta
from typing import Any
from uuid import uuid4, UUID

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from core.config import settings
from src.server.shared.infrastructure.providers.system_clock import get_localized_now

ACCESS_AUD = "access"

_password_hash = PasswordHash((Argon2Hasher(),))
DUMMY_HASHED_PASSWORD = _password_hash.hash("dummy_password")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return _password_hash.hash(password)


def create_token(
        subject: str,
        aud: str,
        ttl: timedelta,
        extra: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Firma un JWT. Devuelve (token, jti)."""
    jti = str(uuid4())
    now = get_localized_now()
    payload = {
        **(extra or {}),  # primero extra: no puede pisar los claims reservados
        "sub": subject,
        "aud": aud,
        "jti": jti,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def decode_token(token: str, aud: str) -> dict[str, Any]:
    """Valida firma, expiración y audiencia. Lanza jwt.InvalidTokenError."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        audience=aud,
        leeway=10,
        options={"require": ["exp", "iat", "sub", "aud", "jti"]},
    )


def create_access_token(user_id: UUID) -> str:
    token, _ = create_token(
        subject=str(user_id),
        aud=ACCESS_AUD,
        ttl=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return token


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def generate_refresh_token() -> tuple[str, str]:
    """Devuelve (token_en_claro, hash). Solo el hash se guarda en la BD."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_refresh_token(raw)
