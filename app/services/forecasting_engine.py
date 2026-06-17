import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Forecast, ScenarioModel
from app.services.cashflow_engine import CashFlowEngine
from app.services.health_engine import FinancialHealthEngine


class ForecastingEngine:
    """Revenue, expense, cash, hiring, and scenario forecasting."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.health_engine = FinancialHealthEngine(session)
        self.cashflow_engine = CashFlowEngine(session)

    async def forecast_revenue(
        self, company_id: uuid.UUID, months_ahead: int = 6
    ) -> list[Forecast]:
        current_monthly = await self.health_engine.calculate_revenue(company_id, 30)
        growth_rate = Decimal("1.05")
        forecasts = []
        for i in range(1, months_ahead + 1):
            period_start = date.today() + timedelta(days=30 * i)
            period_end = period_start + timedelta(days=29)
            predicted = current_monthly * (growth_rate ** i)
            f = Forecast(
                company_id=company_id,
                forecast_type="revenue",
                period_start=period_start,
                period_end=period_end,
                predicted_value=predicted.quantize(Decimal("0.01")),
                confidence_score=Decimal(str(max(50, 90 - i * 5))),
                scenario="base",
            )
            self.session.add(f)
            forecasts.append(f)
        await self.session.flush()
        return forecasts

    async def forecast_expenses(
        self, company_id: uuid.UUID, months_ahead: int = 6
    ) -> list[Forecast]:
        current_monthly = await self.health_engine.calculate_expenses(company_id, 30)
        forecasts = []
        for i in range(1, months_ahead + 1):
            period_start = date.today() + timedelta(days=30 * i)
            period_end = period_start + timedelta(days=29)
            predicted = current_monthly * Decimal("1.02") ** i
            f = Forecast(
                company_id=company_id,
                forecast_type="expense",
                period_start=period_start,
                period_end=period_end,
                predicted_value=predicted.quantize(Decimal("0.01")),
                confidence_score=Decimal(str(max(55, 85 - i * 4))),
                scenario="base",
            )
            self.session.add(f)
            forecasts.append(f)
        await self.session.flush()
        return forecasts

    async def forecast_cash(self, company_id: uuid.UUID, months_ahead: int = 6) -> list[Forecast]:
        cash = await self.cashflow_engine.get_cash_position(company_id)
        burn = await self.cashflow_engine.calculate_monthly_burn(company_id)
        revenue_forecasts = await self.forecast_revenue(company_id, months_ahead)
        expense_forecasts = await self.forecast_expenses(company_id, months_ahead)
        forecasts = []
        balance = cash
        for i in range(months_ahead):
            net = revenue_forecasts[i].predicted_value - expense_forecasts[i].predicted_value
            balance += net
            f = Forecast(
                company_id=company_id,
                forecast_type="cash",
                period_start=revenue_forecasts[i].period_start,
                period_end=revenue_forecasts[i].period_end,
                predicted_value=balance.quantize(Decimal("0.01")),
                confidence_score=Decimal("70"),
                scenario="base",
            )
            self.session.add(f)
            forecasts.append(f)
        await self.session.flush()
        return forecasts

    async def run_scenario(
        self,
        company_id: uuid.UUID,
        name: str,
        scenario_type: str,
        parameters: dict,
        created_by: uuid.UUID | None = None,
    ) -> ScenarioModel:
        base_revenue = await self.health_engine.calculate_revenue(company_id)
        base_expenses = await self.health_engine.calculate_expenses(company_id)
        growth = Decimal(str(parameters.get("revenue_growth_pct", 5))) / Decimal("100")
        expense_growth = Decimal(str(parameters.get("expense_growth_pct", 2))) / Decimal("100")
        hiring_cost = Decimal(str(parameters.get("hiring_cost_monthly", 0)))

        projected_revenue = base_revenue * (Decimal("1") + growth)
        projected_expenses = base_expenses * (Decimal("1") + expense_growth) + hiring_cost
        net = projected_revenue - projected_expenses

        scenario = ScenarioModel(
            company_id=company_id,
            name=name,
            scenario_type=scenario_type,
            parameters=parameters,
            results={
                "projected_revenue": float(projected_revenue),
                "projected_expenses": float(projected_expenses),
                "net_income": float(net),
                "confidence_score": 72,
            },
            created_by=created_by,
        )
        self.session.add(scenario)
        await self.session.flush()
        return scenario

    async def forecast_confidence_score(self, company_id: uuid.UUID) -> Decimal:
        revenue = await self.health_engine.calculate_revenue(company_id)
        if revenue > 0:
            return Decimal("80")
        return Decimal("55")
