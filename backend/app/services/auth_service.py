import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from jose import JWTError


class AuthService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis | None = None) -> None:
        self.repo = UserRepository(session)
        self.redis = redis

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")
        return user

    def issue_tokens(self, user: User) -> tuple[str, str]:
        access = create_access_token(user.id, user.role.value)
        refresh = create_refresh_token(user.id)
        return access, refresh

    async def refresh_access_token(self, refresh_token: str) -> str:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise UnauthorizedError("Refresh token is invalid or expired")

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Wrong token type")

        # Check revocation
        jti = payload.get("jti")
        if jti and self.redis:
            revoked = await self.redis.get(f"revoked:{jti}")
            if revoked:
                raise UnauthorizedError("Refresh token has been revoked")

        user_id = payload.get("sub")
        user = await self.repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or deactivated")

        return create_access_token(user.id, user.role.value)

    async def revoke_token(self, token: str, token_type: str = "access") -> None:
        """Blacklist a token JTI in Redis until its natural expiry."""
        if not self.redis:
            return
        try:
            payload = decode_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if not jti or not exp:
                return
            import time
            ttl = max(int(exp - time.time()), 1)
            await self.redis.setex(f"revoked:{jti}", ttl, "1")
        except JWTError:
            pass  # already invalid — nothing to revoke
