from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.accounting.agent import AccountingAgent
from app.agents.audit.agent import AuditAgent
from app.agents.bank.agent import BankAgent
from app.agents.base import AgentContext, AgentResult
from app.agents.budget.agent import BudgetAgent
from app.agents.cashflow.agent import CashFlowAgent
from app.agents.cfo.agent import CFOAgent
from app.agents.expenses.agent import ExpenseAgent
from app.agents.forecasting.agent import ForecastingAgent
from app.agents.procurement.agent import ProcurementAgent
from app.agents.revenue.agent import RevenueAgent
from app.agents.risk.agent import RiskAgent
from app.agents.tax.agent import TaxAgent
from app.agents.treasury.agent import TreasuryAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

AGENT_PIPELINE = [
    AccountingAgent,
    ExpenseAgent,
    BankAgent,
    CashFlowAgent,
    RevenueAgent,
    BudgetAgent,
    TaxAgent,
    RiskAgent,
    AuditAgent,
    TreasuryAgent,
    ProcurementAgent,
    ForecastingAgent,
]

AGENT_MAP: dict[str, type] = {
    "accounting": AccountingAgent,
    "expenses": ExpenseAgent,
    "bank": BankAgent,
    "cashflow": CashFlowAgent,
    "revenue": RevenueAgent,
    "budget": BudgetAgent,
    "tax": TaxAgent,
    "risk": RiskAgent,
    "audit": AuditAgent,
    "treasury": TreasuryAgent,
    "procurement": ProcurementAgent,
    "forecasting": ForecastingAgent,
    "cfo": CFOAgent,
}


class AgentOrchestrator:
    """Finance AI Network orchestration — sequential agent pipeline culminating in CFO."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def run_pipeline(
        self, company_id: UUID, user_id: UUID | None = None, data: dict[str, Any] | None = None
    ) -> dict:
        context = AgentContext(company_id=company_id, user_id=user_id, data=data or {})
        results: list[AgentResult] = []
        logger.info("pipeline_started", company_id=str(company_id))

        for agent_cls in AGENT_PIPELINE:
            agent = agent_cls(self.session)
            result = await agent.analyze(context)
            results.append(result)
            context.data[agent.name] = result.data
            logger.info("agent_completed", agent=agent.name, score=float(result.score or 0))

        cfo = CFOAgent(self.session)
        cfo_result = await cfo.orchestrate(context)

        return {
            "pipeline": [r.agent for r in results],
            "agent_results": results,
            "cfo": cfo_result,
            "completed_at": datetime.now(UTC).isoformat(),
        }

    async def run_single_agent(
        self, agent_name: str, company_id: UUID, user_id: UUID | None = None
    ) -> AgentResult | dict:
        context = AgentContext(company_id=company_id, user_id=user_id)
        if agent_name == "cfo":
            cfo = CFOAgent(self.session)
            return await cfo.orchestrate(context)
        agent_cls = AGENT_MAP.get(agent_name)
        if not agent_cls:
            raise ValueError(f"Unknown agent: {agent_name}")
        agent = agent_cls(self.session)
        return await agent.analyze(context)
