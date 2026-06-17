import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import Company, User
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.company_repo = CompanyRepository(session)

    @staticmethod
    def _slugify(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        return f"{slug}-{uuid.uuid4().hex[:6]}"

    async def register(self, data: RegisterRequest) -> tuple[User, str, str]:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictError("Email already registered")

        company = Company(
            name=data.company_name,
            slug=self._slugify(data.company_name),
        )
        self.session.add(company)
        await self.session.flush()

        user = User(
            company_id=company.id,
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role.value,
        )
        self.session.add(user)
        await self.session.flush()

        access = create_access_token(user.id, {"role": user.role, "company_id": str(company.id)})
        refresh = create_refresh_token(user.id)
        return user, access, refresh

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is inactive")
        access = create_access_token(
            user.id, {"role": user.role, "company_id": str(user.company_id)}
        )
        refresh = create_refresh_token(user.id)
        return user, access, refresh

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:
            raise UnauthorizedError("Invalid refresh token") from exc
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")
        user = await self.user_repo.get_by_id(uuid.UUID(payload["sub"]))
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        access = create_access_token(
            user.id, {"role": user.role, "company_id": str(user.company_id)}
        )
        new_refresh = create_refresh_token(user.id)
        return access, new_refresh
