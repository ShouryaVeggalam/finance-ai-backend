from decimal import Decimal

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.services.cashflow_engine import CashFlowEngine


class CashFlowAgent(BaseAgent):
    name = "cashflow"
    description = "Cash tracking, forecasting, runway, liquidity analysis"

    async def analyze(self, context: AgentContext) -> AgentResult:
        engine = CashFlowEngine(self.session)
        analysis = await engine.analyze_liquidity(context.company_id)
        runway = await engine.calculate_runway(context.company_id)
        score = Decimal(str(analysis["liquidity_score"]))
        insights = [
            f"Runway: {float(runway.runway_months):.1f} months",
            f"Monthly burn: ${analysis['monthly_burn']:,.2f}",
        ]
        return AgentResult(agent=self.name, score=score, insights=insights, data=analysis)
