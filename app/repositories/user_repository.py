from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id_and_company(self, user_id: UUID, company_id: UUID) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id, User.company_id == company_id)
        )
        return result.scalar_one_or_none()
