from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from src.server.auth.domain import exceptions as e

_ERRORS: dict[type[Exception], tuple[int, str]] = {
    e.InvalidCredentials: (status.HTTP_401_UNAUTHORIZED, "Nombre de usuario o contraseña incorrectos"),
    e.InactiveUser: (status.HTTP_403_FORBIDDEN, "Usuario inactivo"),
    e.InvalidToken: (status.HTTP_401_UNAUTHORIZED, "No se pudieron validar las credenciales"),
    e.InvalidPassword: (status.HTTP_400_BAD_REQUEST, "La contraseña actual es incorrecta"),
    e.SamePassword: (status.HTTP_400_BAD_REQUEST, "La nueva contraseña debe ser diferente a la actual"),
    e.UsernameAlreadyExists: (status.HTTP_409_CONFLICT, "El nombre de usuario ya existe"),
    e.UserNotFound: (status.HTTP_404_NOT_FOUND, "Usuario no encontrado"),
    e.RoleNotFound: (status.HTTP_400_BAD_REQUEST, "Rol no encontrado"),
    e.CannotModifySelf: (status.HTTP_400_BAD_REQUEST, "No puedes realizar esta acción en tu propia cuenta"),
    e.LastActiveAdmin: (status.HTTP_400_BAD_REQUEST, "Debe existir al menos un administrador activo en el sistema"),
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
