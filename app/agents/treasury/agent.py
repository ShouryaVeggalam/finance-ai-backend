from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.services.treasury_engine import TreasuryEngine


class TreasuryAgent(BaseAgent):
    name = "treasury"
    description = "Liquidity planning, reserve management, capital allocation"

    async def analyze(self, context: AgentContext) -> AgentResult:
        engine = TreasuryEngine(self.session)
        position = await engine.get_treasury_position(context.company_id)
        score = await engine.treasury_health_score(context.company_id)
        recommendations = await engine.get_recommendations(context.company_id)
        return AgentResult(
            agent=self.name,
            score=score,
            insights=recommendations,
            data={
                "total_cash": float(position.total_cash),
                "reserve_ratio": float(position.reserve_ratio or 0),
            },
        )
