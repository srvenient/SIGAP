from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from src.server.auth.domain import exceptions as e

_ERRORS: dict[type[Exception], tuple[int, str]] = {
    e.InvalidCredentials: (status.HTTP_401_UNAUTHORIZED, "Incorrect username or password"),
    e.InactiveUser: (status.HTTP_403_FORBIDDEN, "Inactive user"),
    e.InvalidToken: (status.HTTP_401_UNAUTHORIZED, "Could not validate credentials"),
    e.InvalidTwoFactorCode: (status.HTTP_401_UNAUTHORIZED, "Invalid 2FA code"),
    e.InvalidPassword: (status.HTTP_400_BAD_REQUEST, "Current password is incorrect"),
    e.SamePassword: (status.HTTP_400_BAD_REQUEST, "New password must be different from the current one"),
    e.TwoFactorAlreadyEnabled: (status.HTTP_400_BAD_REQUEST, "2FA is already enabled"),
    e.TwoFactorNotEnabled: (status.HTTP_400_BAD_REQUEST, "2FA is not enabled"),
    e.TwoFactorNotInitialized: (status.HTTP_400_BAD_REQUEST, "2FA setup not initialized"),
    e.UsernameAlreadyExists: (status.HTTP_409_CONFLICT, "Username already exists"),
    e.UserNotFound: (status.HTTP_404_NOT_FOUND, "User not found"),
    e.RoleNotFound: (status.HTTP_400_BAD_REQUEST, "Role not found"),
    e.CannotModifySelf: (status.HTTP_400_BAD_REQUEST, "You cannot do this on your own account"),
}


def _make_handler(code: int, detail: str):
    async def handler(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse(status_code=code, content={"detail": detail})

    return handler


async def _account_locked_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, e.AccountLocked)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many failed attempts. Try again later."},
        headers={"Retry-After": str(exc.retry_after)},
    )


async def _rate_limit_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests. Try again later."},
    )


def register_auth_errors(app: FastAPI) -> None:
    for exc_class, (code, detail) in _ERRORS.items():
        app.add_exception_handler(exc_class, _make_handler(code, detail))
    app.add_exception_handler(e.AccountLocked, _account_locked_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
