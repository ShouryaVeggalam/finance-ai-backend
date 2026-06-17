from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BankAccount,
    BankTransaction,
    Budget,
    Customer,
    FinancialHealthScore,
    FinancialInsight,
    Forecast,
    Notification,
    RiskRecord,
    RunwayForecast,
    Vendor,
)
from app.repositories.base import BaseRepository


class BankAccountRepository(BaseRepository[BankAccount]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, BankAccount)

    async def total_cash_position(self, company_id: UUID):
        from decimal import Decimal

        from sqlalchemy import func

        stmt = select(func.coalesce(func.sum(BankAccount.current_balance), 0)).where(
            BankAccount.company_id == company_id,
            BankAccount.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return Decimal(str(result.scalar_one()))


class BankTransactionRepository(BaseRepository[BankTransaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, BankTransaction)


class BudgetRepository(BaseRepository[Budget]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Budget)


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Customer)


class VendorRepository(BaseRepository[Vendor]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Vendor)


class ForecastRepository(BaseRepository[Forecast]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Forecast)


class RiskRecordRepository(BaseRepository[RiskRecord]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RiskRecord)

    async def active_risks(self, company_id: UUID) -> list[RiskRecord]:
        result = await self.session.execute(
            select(RiskRecord).where(
                RiskRecord.company_id == company_id,
                RiskRecord.is_resolved.is_(False),
            )
        )
        return list(result.scalars().all())


class FinancialInsightRepository(BaseRepository[FinancialInsight]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, FinancialInsight)

    async def top_insights(self, company_id: UUID, limit: int = 10) -> list[FinancialInsight]:
        result = await self.session.execute(
            select(FinancialInsight)
            .where(FinancialInsight.company_id == company_id)
            .order_by(FinancialInsight.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Notification)


class HealthScoreRepository(BaseRepository[FinancialHealthScore]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, FinancialHealthScore)

    async def latest(self, company_id: UUID) -> FinancialHealthScore | None:
        result = await self.session.execute(
            select(FinancialHealthScore)
            .where(FinancialHealthScore.company_id == company_id)
            .order_by(FinancialHealthScore.as_of_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class RunwayForecastRepository(BaseRepository[RunwayForecast]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RunwayForecast)

    async def latest(self, company_id: UUID) -> RunwayForecast | None:
        result = await self.session.execute(
            select(RunwayForecast)
            .where(RunwayForecast.company_id == company_id)
            .order_by(RunwayForecast.as_of_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
