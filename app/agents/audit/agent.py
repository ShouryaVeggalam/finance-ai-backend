from decimal import Decimal

from sqlalchemy import func, select

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.models import AuditRecord


class AuditAgent(BaseAgent):
    name = "audit"
    description = "Audit trails, exception detection, compliance validation"

    async def analyze(self, context: AgentContext) -> AgentResult:
        result = await self.session.execute(
            select(func.count()).select_from(AuditRecord).where(
                AuditRecord.company_id == context.company_id
            )
        )
        audit_count = result.scalar_one()
        score = min(Decimal("100"), Decimal(str(audit_count)) / Decimal("10"))
        if score < Decimal("50"):
            score = Decimal("50") + score / Decimal("2")
        insights = [
            f"Audit trail entries: {audit_count}",
            "Audit readiness: " + ("Strong" if audit_count > 100 else "Building"),
        ]
        return AgentResult(
            agent=self.name,
            score=score.quantize(Decimal("0.01")),
            insights=insights,
            data={"audit_trail_count": audit_count},
        )
