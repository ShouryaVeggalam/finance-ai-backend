from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.services.health_engine import FinancialHealthEngine


class BudgetAgent(BaseAgent):
    name = "budget"
    description = "Budget planning, monitoring, and variance analysis"

    async def analyze(self, context: AgentContext) -> AgentResult:
        engine = FinancialHealthEngine(self.session)
        score = await engine.budget_health_score(context.company_id)
        insights = [f"Budget health score: {float(score):.1f}/100"]
        if score < 70:
            insights.append("Budget variances detected — review department allocations")
        return AgentResult(agent=self.name, score=score, insights=insights, data={"budget_health_score": float(score)})
