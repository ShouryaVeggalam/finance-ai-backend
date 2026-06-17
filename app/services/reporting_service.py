import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FinancialReport
from app.services.cashflow_engine import CashFlowEngine
from app.services.forecasting_engine import ForecastingEngine
from app.services.health_engine import FinancialHealthEngine
from app.services.ledger_engine import DoubleEntryLedgerEngine
from app.services.procurement_engine import ProcurementEngine
from app.services.treasury_engine import TreasuryEngine


class ReportingService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.ledger = DoubleEntryLedgerEngine(session)
        self.health = FinancialHealthEngine(session)
        self.cashflow = CashFlowEngine(session)
        self.treasury = TreasuryEngine(session)
        self.procurement = ProcurementEngine(session)
        self.forecasting = ForecastingEngine(session)

    async def generate_report(
        self,
        company_id: uuid.UUID,
        report_type: str,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> FinancialReport:
        period_start = period_start or date.today().replace(day=1)
        period_end = period_end or date.today()
        content: dict

        generators = {
            "profit_and_loss": self._pnl_report,
            "balance_sheet": self._balance_sheet_report,
            "cash_flow": self._cash_flow_report,
            "expense": self._expense_report,
            "budget": self._budget_report,
            "treasury": self._treasury_report,
            "procurement": self._procurement_report,
            "forecast": self._forecast_report,
            "board": self._board_report,
            "executive_cfo": self._executive_cfo_report,
        }

        generator = generators.get(report_type, self._pnl_report)
        content = await generator(company_id, period_start, period_end)

        report = FinancialReport(
            company_id=company_id,
            report_type=report_type,
            title=f"{report_type.replace('_', ' ').title()} Report",
            period_start=period_start,
            period_end=period_end,
            content_json=content,
            generated_by="reporting_engine",
        )
        self.session.add(report)
        await self.session.flush()
        return report

    async def _pnl_report(self, company_id: uuid.UUID, start: date, end: date) -> dict:
        statements = await self.ledger.generate_financial_statements(company_id, start, end)
        return statements["profit_and_loss"]

    async def _balance_sheet_report(self, company_id: uuid.UUID, start: date, end: date) -> dict:
        statements = await self.ledger.generate_financial_statements(company_id, start, end)
        return statements["balance_sheet"]

    async def _cash_flow_report(self, company_id: uuid.UUID, _start: date, _end: date) -> dict:
        return await self.cashflow.analyze_liquidity(company_id)

    async def _expense_report(self, company_id: uuid.UUID, start: date, end: date) -> dict:
        from app.repositories.finance_repository import ExpenseRepository

        repo = ExpenseRepository(self.session)
        total = await repo.total_by_period(company_id, start, end)
        by_dept = await repo.by_department(company_id, start, end)
        return {
            "total": float(total),
            "by_department": {d or "unassigned": float(a) for d, a in by_dept},
        }

    async def _budget_report(self, company_id: uuid.UUID, _start: date, _end: date) -> dict:
        score = await self.health.budget_health_score(company_id)
        return {"budget_health_score": float(score)}

    async def _treasury_report(self, company_id: uuid.UUID, _start: date, _end: date) -> dict:
        position = await self.treasury.get_treasury_position(company_id)
        return {
            "total_cash": float(position.total_cash),
            "reserve_ratio": float(position.reserve_ratio or 0),
            "recommendations": await self.treasury.get_recommendations(company_id),
        }

    async def _procurement_report(self, company_id: uuid.UUID, _start: date, _end: date) -> dict:
        return {
            "vendor_spend": await self.procurement.analyze_vendor_spend(company_id),
            "savings_opportunities": await self.procurement.detect_savings_opportunities(company_id),
        }

    async def _forecast_report(self, company_id: uuid.UUID, _start: date, _end: date) -> dict:
        revenue = await self.forecasting.forecast_revenue(company_id, 3)
        return {
            "revenue_forecast": [
                {"period": f.period_start.isoformat(), "value": float(f.predicted_value)}
                for f in revenue
            ]
        }

    async def _board_report(self, company_id: uuid.UUID, start: date, end: date) -> dict:
        health = await self.health.compute_health_score(company_id)
        runway = await self.cashflow.calculate_runway(company_id)
        return {
            "financial_health_score": float(health.overall_score),
            "runway_months": float(runway.runway_months),
            "revenue": float(await self.health.calculate_revenue(company_id)),
            "expenses": float(await self.health.calculate_expenses(company_id)),
            "period": {"start": start.isoformat(), "end": end.isoformat()},
        }

    async def _executive_cfo_report(self, company_id: uuid.UUID, start: date, end: date) -> dict:
        board = await self._board_report(company_id, start, end)
        treasury = await self._treasury_report(company_id, start, end)
        return {**board, "treasury": treasury, "report_type": "executive_cfo"}
