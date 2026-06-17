from decimal import Decimal

from sqlalchemy import select

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.models import TaxRecord


class TaxAgent(BaseAgent):
    name = "tax"
    description = "Tax classification, liability analysis, compliance monitoring"

    async def analyze(self, context: AgentContext) -> AgentResult:
        result = await self.session.execute(
            select(TaxRecord).where(TaxRecord.company_id == context.company_id)
        )
        records = list(result.scalars().all())
        total_liability = sum(r.liability_amount for r in records)
        unpaid = [r for r in records if r.status != "paid"]
        risk_scores = [r.risk_score for r in records if r.risk_score]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else Decimal("25")
        score = Decimal("100") - avg_risk
        insights = [
            f"Total tax liability: ${float(total_liability):,.2f}",
            f"Unpaid records: {len(unpaid)}",
        ]
        return AgentResult(
            agent=self.name,
            score=score.quantize(Decimal("0.01")),
            insights=insights,
            data={"total_liability": float(total_liability), "unpaid_count": len(unpaid)},
        )
