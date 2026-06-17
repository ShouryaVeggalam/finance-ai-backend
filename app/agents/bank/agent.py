from decimal import Decimal

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.services.banking_engine import BankingEngine


class BankAgent(BaseAgent):
    name = "bank"
    description = "Bank sync, reconciliation, fraud detection, cash position"

    async def analyze(self, context: AgentContext) -> AgentResult:
        engine = BankingEngine(self.session)
        cash = await engine.get_verified_cash_position(context.company_id)
        score = await engine.compute_bank_health_score(context.company_id)
        anomalies = await engine.detect_fraud_anomalies(context.company_id)
        insights = [f"Verified cash position: ${float(cash):,.2f}"]
        if anomalies:
            insights.append(f"Detected {len(anomalies)} potential fraud anomalies")
        return AgentResult(
            agent=self.name,
            score=score,
            insights=insights,
            data={"cash_position": float(cash), "anomalies": anomalies},
        )
