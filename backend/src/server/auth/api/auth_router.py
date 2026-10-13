from typing import Annotated

from fastapi import APIRouter, Request, Response, Depends, Cookie, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import JSONResponse

from core.config import settings
from core.rate_limit import limiter
from src.server.auth.api.deps import AuthServiceDep, SessionUserDep, UserServiceDep
from src.server.auth.domain.exceptions import InvalidToken
from src.server.auth.domain.user.user import UserPublic, UpdatePassword, UpdateProfile

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

ACCESS_COOKIE = "access_token"

REFRESH_COOKIE = "refresh_token"
# El refresh token solo viaja hacia /auth/*, nunca en el resto de la API
REFRESH_COOKIE_PATH = f"{settings.API_V1_STR}/auth"

# Cookie para recordar la preferencia de persistencia en subsecuentes /refresh
REMEMBER_COOKIE = "remember_session"


def _base_cookie_kwargs() -> dict:
    prod = settings.ENVIRONMENT == "production"
    return {
        "httponly": True,
        "secure": prod,
        "samesite": "strict" if prod else "lax",
    }


def _set_session_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    remember_me: bool = True
) -> None:
    # Si remember_me es True, las cookies tienen max_age (permanecen 7 días tras cerrar el navegador)
    # Si remember_me es False, max_age es None (Session Cookie: se elimina automáticamente al cerrar el navegador)
    access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 if remember_me else None
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600 if remember_me else None

    response.set_cookie(
        ACCESS_COOKIE, access_token,
        max_age=access_max_age,
        path="/",
        **_base_cookie_kwargs(),
    )
    response.set_cookie(
        REFRESH_COOKIE, refresh_token,
        max_age=refresh_max_age,
        path=REFRESH_COOKIE_PATH,
        **_base_cookie_kwargs(),
    )
    response.set_cookie(
        REMEMBER_COOKIE, "1" if remember_me else "0",
        max_age=refresh_max_age,
        path=REFRESH_COOKIE_PATH,
        **_base_cookie_kwargs(),
    )


def _clear_session_cookies(response: Response) -> None:
    # Deben coincidir path y atributos con los de set_cookie para que el navegador las borre
    response.delete_cookie(ACCESS_COOKIE, path="/", **_base_cookie_kwargs())
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH, **_base_cookie_kwargs())
    response.delete_cookie(REMEMBER_COOKIE, path=REFRESH_COOKIE_PATH, **_base_cookie_kwargs())


def _unauthorized_and_clear(detail: str) -> JSONResponse:
    resp = JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": detail})
    _clear_session_cookies(resp)
    return resp


@auth_router.post("/login")
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login(
        request: Request,
        response: Response,
        form: Annotated[OAuth2PasswordRequestForm, Depends()],
        auth_service: AuthServiceDep,
        remember_me: Annotated[bool, Form()] = False,
):
    result = await auth_service.authenticate(form.username, form.password)
    _set_session_cookies(response, result.access_token, result.refresh_token, remember_me=remember_me)
    return {
        "detail": "Login successful",
        "must_change_password": result.user.must_change_password,
    }


@auth_router.post("/refresh")
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def refresh(
        request: Request,
        response: Response,
        auth_service: AuthServiceDep,
        refresh_token: Annotated[str | None, Cookie()] = None,
        remember_session: Annotated[str | None, Cookie()] = None,
):
    if not refresh_token:
        return _unauthorized_and_clear("Not authenticated")

    try:
        result = await auth_service.refresh(refresh_token)
    except InvalidToken:
        return _unauthorized_and_clear("Could not validate credentials")

    is_remember = remember_session == "1"
    _set_session_cookies(response, result.access_token, result.refresh_token, remember_me=is_remember)
    return {"detail": "Session refreshed", "must_change_password": result.user.must_change_password}


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
        response: Response,
        auth_service: AuthServiceDep,
        refresh_token: Annotated[str | None, Cookie()] = None,
):
    if refresh_token:
        await auth_service.logout(refresh_token)
    _clear_session_cookies(response)


@auth_router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(response: Response, user: SessionUserDep, auth_service: AuthServiceDep):
    await auth_service.logout_all(user)
    _clear_session_cookies(response)


@auth_router.get("/me", response_model=UserPublic)
async def me(user: SessionUserDep):
    return user


@auth_router.patch("/profile", response_model=UserPublic)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def update_profile(
        request: Request,
        body: UpdateProfile,
        user: SessionUserDep,
        user_service: UserServiceDep,
):
    updated = await user_service.update_profile(user, body)
    return UserPublic.model_validate(updated)


@auth_router.post("/change-password")
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def change_password(
        request: Request,
        response: Response,
        body: UpdatePassword,
        user: SessionUserDep,  # permitido aunque must_change_password sea True
        auth_service: AuthServiceDep,
        remember_session: Annotated[str | None, Cookie()] = None,
):
    access, refresh_token = await auth_service.change_password(
        user, body.current_password, body.new_password
    )
    is_remember = remember_session == "1"
    _set_session_cookies(response, access, refresh_token, remember_me=is_remember)
    return {"detail": "Password updated"}

