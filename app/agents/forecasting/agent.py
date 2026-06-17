from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.services.forecasting_engine import ForecastingEngine


class ForecastingAgent(BaseAgent):
    name = "forecasting"
    description = "Revenue, expense, cash forecasting and scenario planning"

    async def analyze(self, context: AgentContext) -> AgentResult:
        engine = ForecastingEngine(self.session)
        confidence = await engine.forecast_confidence_score(context.company_id)
        revenue_fc = await engine.forecast_revenue(context.company_id, 3)
        insights = [
            f"Forecast confidence: {float(confidence):.0f}%",
            f"3-month revenue projection: ${sum(float(f.predicted_value) for f in revenue_fc):,.2f}",
        ]
        return AgentResult(
            agent=self.name,
            score=confidence,
            insights=insights,
            data={
                "confidence_score": float(confidence),
                "revenue_forecast": [
                    {"period": f.period_start.isoformat(), "value": float(f.predicted_value)}
                    for f in revenue_fc
                ],
            },
        )
