from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.roles import UserRole, role_at_least
from app.core.security import TOKEN_TYPE_ACCESS, decode_token
from app.database.session import get_db
from app.models import User
from app.repositories.user_repository import UserRepository

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise UnauthorizedError("Missing authentication token")
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise UnauthorizedError("Invalid authentication token") from exc
    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise UnauthorizedError("Invalid token type")
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")
    repo = UserRepository(db)
    user = await repo.get_by_id(UUID(user_id))
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user


def require_roles(*roles: UserRole):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = UserRole(current_user.role)
        allowed = {r.value for r in roles}
        if user_role.value in allowed or any(role_at_least(user_role, r) for r in roles):
            return current_user
        raise ForbiddenError(f"Requires one of: {', '.join(sorted(allowed))}")

    return checker


async def get_company_id(
    current_user: User = Depends(get_current_user),
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
) -> UUID:
    if x_company_id and current_user.role == UserRole.ADMIN.value:
        return UUID(x_company_id)
    return current_user.company_id
