from typing import Annotated

from fastapi import APIRouter, Request, Response, Depends
from fastapi.security import OAuth2PasswordRequestForm

from core.config import settings
from core.rate_limit import limiter
from server.auth.api.deps import AuthServiceDep

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

ACCESS_COOKIE = "access_token"

REFRESH_COOKIE = "refresh_token"
# El refresh token solo viaja hacia /auth/*, nunca en el resto de la API
REFRESH_COOKIE_PATH = f"{settings.API_V1_STR}/auth"


def _base_cookie_kwargs() -> dict:
    prod = settings.ENVIRONMENT == "production"
    return {
        "httponly": True,
        "secure": prod,
        "samesite": "strict" if prod else "lax",
    }


def _set_session_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        ACCESS_COOKIE, access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        **_base_cookie_kwargs(),
    )
    response.set_cookie(
        REFRESH_COOKIE, refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path=REFRESH_COOKIE_PATH,
        **_base_cookie_kwargs(),
    )


def _clear_session_cookies(response: Response) -> None:
    # Deben coincidir path y atributos con los de set_cookie para que el navegador las borre
    response.delete_cookie(ACCESS_COOKIE, path="/", **_base_cookie_kwargs())
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH, **_base_cookie_kwargs())


@auth_router.post("/login")
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login(
        request: Request,
        response: Response,
        form: Annotated[OAuth2PasswordRequestForm, Depends()],
        auth_service: AuthServiceDep,
):
    result = await auth_service.authenticate(form.username, form.password)
    _set_session_cookies(response, result.access_token, result.refresh_token)
    return {
        "detail": "Login successful",
        "must_change_password": result.user.must_change_password,
    }
