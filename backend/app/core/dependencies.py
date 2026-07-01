from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)

# ─── Redis client (module-level, shared) ─────────────────────────────────────

_redis_client: aioredis.Redis | None = None


def set_redis_client(client: aioredis.Redis) -> None:
    global _redis_client
    _redis_client = client


def get_redis() -> aioredis.Redis | None:
    return _redis_client


# ─── DB dependency ────────────────────────────────────────────────────────────

DBSession = Annotated[AsyncSession, Depends(get_db)]


# ─── Auth token extraction ────────────────────────────────────────────────────

async def _extract_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    raise UnauthorizedError("Missing or invalid Authorization header")


async def _get_current_user(
    token: Annotated[str, Depends(_extract_token)],
    session: DBSession,
) -> User:
    try:
        payload = decode_token(token)
    except JWTError:
        raise UnauthorizedError("Token is invalid or expired")

    if payload.get("type") != "access":
        raise UnauthorizedError("Wrong token type")

    # Check if token is blacklisted (logout)
    jti = payload.get("jti")
    if jti and _redis_client is not None:
        is_revoked = await _redis_client.get(f"revoked:{jti}")
        if is_revoked:
            raise UnauthorizedError("Token has been revoked")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Malformed token payload")

    repo = UserRepository(session)
    user = await repo.get_by_id(UUID(user_id))
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or deactivated")

    return user


CurrentUser = Annotated[User, Depends(_get_current_user)]


# ─── Role guards ──────────────────────────────────────────────────────────────

def require_roles(*roles: UserRole):
    """
    FastAPI dependency factory.
    Usage: Depends(require_roles(UserRole.DOCTOR, UserRole.ADMIN))
    """
    async def _check(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise ForbiddenError(
                f"Access restricted to: {[r.value for r in roles]}"
            )
        return current_user
    return _check


def require_doctor():
    return require_roles(UserRole.DOCTOR, UserRole.ADMIN)


def require_laboratorian():
    return require_roles(UserRole.LABORATORIAN, UserRole.ADMIN)


def require_admin():
    return require_roles(UserRole.ADMIN)


def require_patient():
    return require_roles(UserRole.PATIENT, UserRole.ADMIN)


# ─── Audit log context ────────────────────────────────────────────────────────

def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_user_agent(request: Request) -> str | None:
    return request.headers.get("User-Agent")
