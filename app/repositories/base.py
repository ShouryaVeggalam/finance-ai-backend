from collections.abc import Sequence
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: type[ModelT]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: UUID, company_id: UUID | None = None) -> ModelT | None:
        stmt = select(self.model).where(self.model.id == id)
        if company_id is not None and hasattr(self.model, "company_id"):
            stmt = stmt.where(self.model.company_id == company_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_company(
        self, company_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> Sequence[ModelT]:
        stmt = (
            select(self.model)
            .where(self.model.company_id == company_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_company(self, company_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.company_id == company_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelT) -> ModelT:
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)
        await self.session.flush()
