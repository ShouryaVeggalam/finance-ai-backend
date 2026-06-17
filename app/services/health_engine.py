import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Budget, Customer, FinancialHealthScore
from app.repositories.domain_repository import BudgetRepository, HealthScoreRepository
from app.repositories.finance_repository import ExpenseRepository, TransactionRepository
from app.services.cashflow_engine import CashFlowEngine


class FinancialHealthEngine:
    """Composite financial health scoring across profitability, liquidity, growth, budget, risk."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tx_repo = TransactionRepository(session)
        self.expense_repo = ExpenseRepository(session)
        self.budget_repo = BudgetRepository(session)
        self.health_repo = HealthScoreRepository(session)
        self.cashflow_engine = CashFlowEngine(session)

    async def calculate_revenue(self, company_id: uuid.UUID, days: int = 30) -> Decimal:
        end = date.today()
        start = end - timedelta(days=days)
        return await self.tx_repo.sum_by_type(company_id, "revenue", start, end)

    async def calculate_expenses(self, company_id: uuid.UUID, days: int = 30) -> Decimal:
        end = date.today()
        start = end - timedelta(days=days)
        ledger_expenses = await self.tx_repo.sum_by_type(company_id, "expense", start, end)
        operational = await self.expense_repo.total_by_period(company_id, start, end)
        return ledger_expenses + operational

    async def profitability_score(self, company_id: uuid.UUID) -> Decimal:
        revenue = await self.calculate_revenue(company_id)
        expenses = await self.calculate_expenses(company_id)
        if revenue <= 0:
            return Decimal("0")
        margin = ((revenue - expenses) / revenue) * Decimal("100")
        return max(Decimal("0"), min(Decimal("100"), margin + Decimal("50")))

    async def growth_score(self, company_id: uuid.UUID) -> Decimal:
        result = await self.session.execute(
            select(func.coalesce(func.sum(Customer.mrr), 0)).where(
                Customer.company_id == company_id,
                Customer.is_active.is_(True),
            )
        )
        mrr = Decimal(str(result.scalar_one()))
        if mrr <= 0:
            return Decimal("50")
        return min(Decimal("100"), mrr / Decimal("1000"))

    async def budget_health_score(self, company_id: uuid.UUID) -> Decimal:
        budgets = await self.budget_repo.list_by_company(company_id, limit=1000)
        if not budgets:
            return Decimal("75")
        variances = []
        for b in budgets:
            if b.allocated_amount > 0:
                utilization = (b.spent_amount / b.allocated_amount) * Decimal("100")
                variances.append(abs(utilization - Decimal("100")))
        if not variances:
            return Decimal("75")
        avg_variance = sum(variances) / len(variances)
        return max(Decimal("0"), Decimal("100") - avg_variance)

    async def compute_health_score(self, company_id: uuid.UUID) -> FinancialHealthScore:
        profitability = await self.profitability_score(company_id)
        liquidity_data = await self.cashflow_engine.analyze_liquidity(company_id)
        liquidity = Decimal(str(liquidity_data["liquidity_score"]))
        growth = await self.growth_score(company_id)
        budget = await self.budget_health_score(company_id)

        from app.repositories.domain_repository import RiskRecordRepository

        risks = await RiskRecordRepository(self.session).active_risks(company_id)
        risk_penalty = min(Decimal("50"), Decimal(str(len(risks) * 5)))
        risk = Decimal("100") - risk_penalty

        overall = (profitability + liquidity + growth + budget + risk) / Decimal("5")
        score = FinancialHealthScore(
            company_id=company_id,
            as_of_date=date.today(),
            overall_score=overall.quantize(Decimal("0.01")),
            profitability_score=profitability.quantize(Decimal("0.01")),
            liquidity_score=liquidity.quantize(Decimal("0.01")),
            growth_score=growth.quantize(Decimal("0.01")),
            budget_score=budget.quantize(Decimal("0.01")),
            risk_score=risk.quantize(Decimal("0.01")),
            breakdown={
                "profitability": float(profitability),
                "liquidity": float(liquidity),
                "growth": float(growth),
                "budget": float(budget),
                "risk": float(risk),
            },
        )
        self.session.add(score)
        await self.session.flush()
        return score
