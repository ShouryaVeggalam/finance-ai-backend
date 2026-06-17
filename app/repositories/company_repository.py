from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Company)

    async def get_by_slug(self, slug: str) -> Company | None:
        result = await self.session.execute(select(Company).where(Company.slug == slug))
        return result.scalar_one_or_none()

    async def get_active(self, company_id: UUID) -> Company | None:
        result = await self.session.execute(
            select(Company).where(Company.id == company_id, Company.is_active.is_(True))
        )
        return result.scalar_one_or_none()
