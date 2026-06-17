from decimal import Decimal

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.repositories.domain_repository import RiskRecordRepository


class RiskAgent(BaseAgent):
    name = "risk"
    description = "Financial risk detection across cash, liquidity, vendor, revenue, fraud"

    async def analyze(self, context: AgentContext) -> AgentResult:
        repo = RiskRecordRepository(self.session)
        risks = await repo.active_risks(context.company_id)
        if not risks:
            return AgentResult(
                agent=self.name,
                score=Decimal("90"),
                insights=["No active financial risks detected"],
                data={"active_risks": 0},
            )
        avg_score = sum(r.score for r in risks) / len(risks)
        critical = [r for r in risks if r.risk_level == "critical"]
        insights = [f"Active risks: {len(risks)}", f"Critical risks: {len(critical)}"]
        for r in risks[:3]:
            insights.append(f"[{r.risk_level}] {r.risk_type}: {r.description or 'No description'}")
        return AgentResult(
            agent=self.name,
            score=max(Decimal("0"), Decimal("100") - avg_score),
            insights=insights,
            data={"risks": [{"type": r.risk_type, "level": r.risk_level, "score": float(r.score)} for r in risks]},
        )
