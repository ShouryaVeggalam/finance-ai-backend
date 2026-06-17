import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CashFlow, RunwayForecast
from app.repositories.domain_repository import BankAccountRepository, RunwayForecastRepository
from app.repositories.finance_repository import ExpenseRepository, TransactionRepository


class CashFlowEngine:
    """Cash tracking, forecasting, runway, and liquidity analysis."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.bank_repo = BankAccountRepository(session)
        self.expense_repo = ExpenseRepository(session)
        self.tx_repo = TransactionRepository(session)
        self.runway_repo = RunwayForecastRepository(session)

    async def get_cash_position(self, company_id: uuid.UUID) -> Decimal:
        return await self.bank_repo.total_cash_position(company_id)

    async def calculate_monthly_burn(self, company_id: uuid.UUID) -> Decimal:
        end = date.today()
        start = end - timedelta(days=30)
        expenses = await self.expense_repo.total_by_period(company_id, start, end)
        outflows = await self.tx_repo.sum_by_type(company_id, "expense", start, end)
        return expenses + outflows

    async def calculate_runway(self, company_id: uuid.UUID) -> RunwayForecast:
        cash = await self.get_cash_position(company_id)
        burn = await self.calculate_monthly_burn(company_id)
        if burn <= 0:
            runway_months = Decimal("999")
            zero_date = None
        else:
            runway_months = (cash / burn).quantize(Decimal("0.01"))
            zero_date = date.today() + timedelta(days=int(runway_months * 30))

        forecast = RunwayForecast(
            company_id=company_id,
            as_of_date=date.today(),
            cash_balance=cash,
            monthly_burn=burn,
            runway_months=runway_months,
            zero_cash_date=zero_date,
            assumptions={"burn_calculation_days": 30},
        )
        self.session.add(forecast)
        await self.session.flush()
        return forecast

    async def analyze_liquidity(self, company_id: uuid.UUID) -> dict:
        cash = await self.get_cash_position(company_id)
        burn = await self.calculate_monthly_burn(company_id)
        runway = await self.calculate_runway(company_id)
        liquidity_score = min(Decimal("100"), (runway.runway_months / Decimal("12")) * Decimal("100"))
        return {
            "cash_position": float(cash),
            "monthly_burn": float(burn),
            "runway_months": float(runway.runway_months),
            "liquidity_score": float(liquidity_score.quantize(Decimal("0.01"))),
            "zero_cash_date": runway.zero_cash_date.isoformat() if runway.zero_cash_date else None,
        }

    async def record_cash_flow_period(
        self,
        company_id: uuid.UUID,
        period_start: date,
        period_end: date,
        opening_balance: Decimal,
        inflows: Decimal,
        outflows: Decimal,
    ) -> CashFlow:
        cf = CashFlow(
            company_id=company_id,
            period_start=period_start,
            period_end=period_end,
            opening_balance=opening_balance,
            closing_balance=opening_balance + inflows - outflows,
            inflows=inflows,
            outflows=outflows,
            net_cash_flow=inflows - outflows,
        )
        self.session.add(cf)
        await self.session.flush()
        return cf

    async def compute_cash_flow_score(self, company_id: uuid.UUID) -> Decimal:
        analysis = await self.analyze_liquidity(company_id)
        return Decimal(str(analysis["liquidity_score"]))
