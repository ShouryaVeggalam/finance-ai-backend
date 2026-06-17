from decimal import Decimal

from sqlalchemy import func, select

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.models import Customer
from app.services.health_engine import FinancialHealthEngine


class RevenueAgent(BaseAgent):
    name = "revenue"
    description = "Revenue tracking, MRR/ARR analysis, growth metrics"

    async def analyze(self, context: AgentContext) -> AgentResult:
        health = FinancialHealthEngine(self.session)
        revenue = await health.calculate_revenue(context.company_id)
        result = await self.session.execute(
            select(
                func.coalesce(func.sum(Customer.mrr), 0),
                func.coalesce(func.sum(Customer.arr), 0),
                func.count(),
            ).where(Customer.company_id == context.company_id, Customer.is_active.is_(True))
        )
        mrr, arr, count = result.one()
        growth_score = await health.growth_score(context.company_id)
        insights = [
            f"Revenue (30d): ${float(revenue):,.2f}",
            f"MRR: ${float(mrr):,.2f} | ARR: ${float(arr):,.2f}",
            f"Active customers: {count}",
        ]
        return AgentResult(
            agent=self.name,
            score=growth_score,
            insights=insights,
            data={"revenue": float(revenue), "mrr": float(mrr), "arr": float(arr), "customers": count},
        )
