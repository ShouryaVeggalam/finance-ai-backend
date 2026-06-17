from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.services.procurement_engine import ProcurementEngine


class ProcurementAgent(BaseAgent):
    name = "procurement"
    description = "Vendor management, contract monitoring, spend optimization"

    async def analyze(self, context: AgentContext) -> AgentResult:
        engine = ProcurementEngine(self.session)
        score = await engine.procurement_health_score(context.company_id)
        savings = await engine.detect_savings_opportunities(context.company_id)
        alerts = await engine.vendor_risk_alerts(context.company_id)
        insights = [f"Procurement health: {float(score):.1f}/100"]
        insights.extend(f"Savings opportunity: {s['vendor_name']}" for s in savings[:3])
        insights.extend(f"Vendor risk alert: {a['name']}" for a in alerts[:3])
        return AgentResult(
            agent=self.name,
            score=score,
            insights=insights,
            data={"savings_opportunities": savings, "vendor_alerts": alerts},
        )
