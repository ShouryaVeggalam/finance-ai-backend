from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog
from app.repositories.domain_repository import FinancialInsightRepository, HealthScoreRepository
from app.schemas.dashboard import DashboardResponse
from app.services.banking_engine import BankingEngine
from app.services.cashflow_engine import CashFlowEngine
from app.services.forecasting_engine import ForecastingEngine
from app.services.health_engine import FinancialHealthEngine
from app.services.procurement_engine import ProcurementEngine
from app.services.treasury_engine import TreasuryEngine


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.health_engine = FinancialHealthEngine(session)
        self.cashflow_engine = CashFlowEngine(session)
        self.banking_engine = BankingEngine(session)
        self.treasury_engine = TreasuryEngine(session)
        self.procurement_engine = ProcurementEngine(session)
        self.forecasting_engine = ForecastingEngine(session)
        self.insight_repo = FinancialInsightRepository(session)
        self.health_repo = HealthScoreRepository(session)

    async def get_dashboard(self, company_id: UUID) -> DashboardResponse:
        revenue = await self.health_engine.calculate_revenue(company_id)
        expenses = await self.health_engine.calculate_expenses(company_id)
        cash = await self.cashflow_engine.get_cash_position(company_id)
        runway = await self.cashflow_engine.calculate_runway(company_id)
        health = await self.health_engine.compute_health_score(company_id)
        budget_score = await self.health_engine.budget_health_score(company_id)
        bank_score = await self.banking_engine.compute_bank_health_score(company_id)
        treasury_score = await self.treasury_engine.treasury_health_score(company_id)
        procurement_score = await self.procurement_engine.procurement_health_score(company_id)
        liquidity = await self.cashflow_engine.analyze_liquidity(company_id)
        allocations = await self.treasury_engine.get_capital_allocations(company_id)
        confidence = await self.forecasting_engine.forecast_confidence_score(company_id)
        insights = await self.insight_repo.top_insights(company_id, limit=5)

        activity_result = await self.session.execute(
            select(ActivityLog)
            .where(ActivityLog.company_id == company_id)
            .order_by(ActivityLog.created_at.desc())
            .limit(10)
        )
        activities = activity_result.scalars().all()

        treasury_recs = await self.treasury_engine.get_recommendations(company_id)
        savings = await self.procurement_engine.detect_savings_opportunities(company_id)
        cfo_recs = treasury_recs + [
            f"Potential savings with {s['vendor_name']}: ${s['estimated_savings']:,.0f}"
            for s in savings[:3]
        ]

        return DashboardResponse(
            revenue=revenue,
            expenses=expenses,
            cash_position=cash,
            runway_months=runway.runway_months,
            financial_health_score=health.overall_score,
            budget_health_score=budget_score,
            bank_health_score=bank_score,
            treasury_health_score=treasury_score,
            procurement_health_score=procurement_score,
            risk_score=health.risk_score,
            liquidity_position=liquidity["cash_position"],
            capital_allocation={
                "items": [
                    {
                        "category": a.category,
                        "allocated": float(a.allocated_amount),
                        "utilized": float(a.utilized_amount),
                    }
                    for a in allocations
                ]
            },
            forecast_summary={
                "confidence_score": float(confidence),
                "runway_months": float(runway.runway_months),
            },
            top_insights=[
                {
                    "id": str(i.id),
                    "title": i.title,
                    "summary": i.summary,
                    "severity": i.severity,
                    "agent": i.agent_source,
                }
                for i in insights
            ],
            cfo_recommendations=cfo_recs or ["Financial position is stable — continue monitoring"],
            recent_activity=[
                {
                    "action": a.action,
                    "resource_type": a.resource_type,
                    "created_at": a.created_at.isoformat(),
                }
                for a in activities
            ],
            generated_at=datetime.now(UTC),
        )
