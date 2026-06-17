import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CapitalAllocation, LiquidityForecast, TreasuryPosition
from app.repositories.domain_repository import BankAccountRepository
from app.services.cashflow_engine import CashFlowEngine


class TreasuryEngine:
    """Liquidity planning, reserve management, and capital allocation."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.bank_repo = BankAccountRepository(session)
        self.cashflow_engine = CashFlowEngine(session)

    async def get_treasury_position(self, company_id: uuid.UUID) -> TreasuryPosition:
        total_cash = await self.bank_repo.total_cash_position(company_id)
        burn = await self.cashflow_engine.calculate_monthly_burn(company_id)
        reserve_months = Decimal("3")
        required_reserve = burn * reserve_months
        reserve_ratio = (total_cash / required_reserve) if required_reserve > 0 else Decimal("1")

        position = TreasuryPosition(
            company_id=company_id,
            as_of_date=date.today(),
            total_cash=total_cash,
            total_investments=Decimal("0"),
            total_debt=Decimal("0"),
            net_position=total_cash,
            reserve_ratio=reserve_ratio.quantize(Decimal("0.0001")),
        )
        self.session.add(position)
        await self.session.flush()
        return position

    async def forecast_liquidity(
        self, company_id: uuid.UUID, days_ahead: int = 90
    ) -> LiquidityForecast:
        cash = await self.bank_repo.total_cash_position(company_id)
        burn = await self.cashflow_engine.calculate_monthly_burn(company_id)
        daily_burn = burn / Decimal("30")
        projected = cash - (daily_burn * Decimal(str(days_ahead)))
        minimum = burn * Decimal("2")

        forecast = LiquidityForecast(
            company_id=company_id,
            forecast_date=date.today(),
            projected_balance=projected.quantize(Decimal("0.01")),
            minimum_required=minimum.quantize(Decimal("0.01")),
            surplus_deficit=(projected - minimum).quantize(Decimal("0.01")),
            confidence_score=Decimal("75"),
        )
        self.session.add(forecast)
        await self.session.flush()
        return forecast

    async def get_capital_allocations(self, company_id: uuid.UUID) -> list[CapitalAllocation]:
        result = await self.session.execute(
            select(CapitalAllocation).where(CapitalAllocation.company_id == company_id)
        )
        return list(result.scalars().all())

    async def allocate_capital(
        self,
        company_id: uuid.UUID,
        category: str,
        amount: Decimal,
        period_start: date,
        period_end: date,
    ) -> CapitalAllocation:
        allocation = CapitalAllocation(
            company_id=company_id,
            category=category,
            allocated_amount=amount,
            period_start=period_start,
            period_end=period_end,
        )
        self.session.add(allocation)
        await self.session.flush()
        return allocation

    async def treasury_health_score(self, company_id: uuid.UUID) -> Decimal:
        position = await self.get_treasury_position(company_id)
        ratio = position.reserve_ratio or Decimal("0")
        return min(Decimal("100"), ratio * Decimal("33.33")).quantize(Decimal("0.01"))

    async def get_recommendations(self, company_id: uuid.UUID) -> list[str]:
        position = await self.get_treasury_position(company_id)
        recommendations = []
        if position.reserve_ratio and position.reserve_ratio < Decimal("1"):
            recommendations.append(
                "Increase cash reserves to maintain 3-month operating runway minimum"
            )
        if position.total_cash > position.total_debt * Decimal("10"):
            recommendations.append("Consider short-term investment vehicles for excess cash")
        if not recommendations:
            recommendations.append("Treasury position is healthy — maintain current allocation")
        return recommendations
