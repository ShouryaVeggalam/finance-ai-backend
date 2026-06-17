from datetime import UTC, datetime
from decimal import Decimal

from app.agents.accounting.agent import AccountingAgent
from app.agents.audit.agent import AuditAgent
from app.agents.bank.agent import BankAgent
from app.agents.base import AgentContext, AgentResult
from app.agents.budget.agent import BudgetAgent
from app.agents.cashflow.agent import CashFlowAgent
from app.agents.expenses.agent import ExpenseAgent
from app.agents.forecasting.agent import ForecastingAgent
from app.agents.procurement.agent import ProcurementAgent
from app.agents.revenue.agent import RevenueAgent
from app.agents.risk.agent import RiskAgent
from app.agents.tax.agent import TaxAgent
from app.agents.treasury.agent import TreasuryAgent
from app.models import FinancialInsight
from app.services.health_engine import FinancialHealthEngine
from sqlalchemy.ext.asyncio import AsyncSession


class CFOAgent:
    """AI Chief Financial Officer — consumes all agent outputs for executive intelligence."""

    name = "cfo"

    def __init__(self, session: AsyncSession):
        self.session = session
        self.agents = [
            AccountingAgent(session),
            ExpenseAgent(session),
            BankAgent(session),
            CashFlowAgent(session),
            RevenueAgent(session),
            BudgetAgent(session),
            TaxAgent(session),
            RiskAgent(session),
            AuditAgent(session),
            TreasuryAgent(session),
            ProcurementAgent(session),
            ForecastingAgent(session),
        ]

    async def orchestrate(self, context: AgentContext) -> dict:
        results: list[AgentResult] = []
        for agent in self.agents:
            result = await agent.analyze(context)
            results.append(result)
            insight = FinancialInsight(
                company_id=context.company_id,
                insight_type=result.agent,
                title=f"{result.agent.title()} Intelligence Update",
                summary="; ".join(result.insights[:2]) if result.insights else "Analysis complete",
                severity="info" if (result.score or 0) >= 70 else "warning",
                agent_source=result.agent,
                data_json=result.data,
            )
            self.session.add(insight)

        health_engine = FinancialHealthEngine(self.session)
        health = await health_engine.compute_health_score(context.company_id)

        executive_summary = await self._generate_executive_summary(context, results, health.overall_score)
        recommendations = self._strategic_recommendations(results)

        await self.session.flush()
        return {
            "agent": self.name,
            "status": "success",
            "executive_summary": executive_summary,
            "financial_health_score": float(health.overall_score),
            "agent_results": [
                {
                    "agent": r.agent,
                    "score": float(r.score) if r.score else None,
                    "insights": r.insights,
                }
                for r in results
            ],
            "strategic_recommendations": recommendations,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def answer_question(self, context: AgentContext, question: str) -> dict:
        orchestration = await self.orchestrate(context)
        from app.agents.base import BaseAgent

        base = BaseAgent(self.session)
        answer = await base._llm_analyze(
            "You are an AI CFO for a finance operating system. Answer executive financial questions "
            "concisely with actionable recommendations based on the provided data.",
            f"Question: {question}\n\nFinancial Data: {orchestration}",
        )
        return {
            "question": question,
            "answer": answer,
            "financial_health_score": orchestration["financial_health_score"],
            "recommendations": orchestration["strategic_recommendations"],
        }

    async def _generate_executive_summary(
        self, context: AgentContext, results: list[AgentResult], health_score: Decimal
    ) -> str:
        from app.agents.base import BaseAgent

        base = BaseAgent(self.session)
        summary_data = {r.agent: {"score": float(r.score or 0), "insights": r.insights[:2]} for r in results}
        return await base._llm_analyze(
            "Generate a concise executive financial summary for leadership.",
            f"Health Score: {float(health_score)}. Agent data: {summary_data}",
        )

    def _strategic_recommendations(self, results: list[AgentResult]) -> list[str]:
        recs = []
        scores = {r.agent: r.score for r in results if r.score is not None}
        if scores.get("cashflow", 100) < 60:
            recs.append("Prioritize cash conservation — runway is below healthy threshold")
        if scores.get("risk", 100) < 70:
            recs.append("Address active financial risks immediately")
        if scores.get("procurement", 100) < 75:
            recs.append("Review vendor contracts for savings opportunities")
        if scores.get("revenue", 100) > 80:
            recs.append("Strong revenue growth — consider strategic expansion investments")
        if not recs:
            recs.append("Maintain current financial discipline and continue monitoring KPIs")
        return recs
