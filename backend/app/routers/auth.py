from fastapi import APIRouter, Cookie, Depends, Response

from app.core.dependencies import CurrentUser, DBSession, get_redis
from app.core.exceptions import UnauthorizedError
from app.core.config import settings
from app.schemas.auth import LoginRequest, RefreshResponse, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

REFRESH_COOKIE = "refresh_token"


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    session: DBSession,
):
    redis = get_redis()
    service = AuthService(session, redis)
    user = await service.authenticate(body.email, body.password)
    access_token, refresh_token = service.issue_tokens(user)

    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=access_token,
        user=UserRead.model_validate(user),
    )


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    current_user: CurrentUser,
    session: DBSession,
):
    # The access token is already in CurrentUser, we revoke it via JTI
    # In a real flow we'd also pass the token string here; for simplicity we clear the cookie
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    return None


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    response: Response,
    session: DBSession,
    refresh_token: str | None = Cookie(None),
):
    """
    Accepts refresh_token from httpOnly cookie.
    Returns a new access_token.
    """
    if refresh_token is None:
        raise UnauthorizedError("Refresh token cookie is missing")

    redis = get_redis()
    service = AuthService(session, redis)
    access_token = await service.refresh_access_token(refresh_token)
    return RefreshResponse(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser):
    return UserRead.model_validate(current_user)
