from datetime import date, timedelta
from decimal import Decimal

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.repositories.finance_repository import ExpenseRepository


class ExpenseAgent(BaseAgent):
    name = "expenses"
    description = "Expense categorization, spend analysis, and cost optimization"

    async def analyze(self, context: AgentContext) -> AgentResult:
        repo = ExpenseRepository(self.session)
        end = date.today()
        start = end - timedelta(days=30)
        total = await repo.total_by_period(context.company_id, start, end)
        by_dept = await repo.by_department(context.company_id, start, end)
        insights = [f"Total expenses (30d): ${float(total):,.2f}"]
        for dept, amount in by_dept[:5]:
            insights.append(f"Department {dept or 'unassigned'}: ${float(amount):,.2f}")
        score = Decimal("80") if total > 0 else Decimal("50")
        return AgentResult(
            agent=self.name,
            score=score,
            insights=insights,
            data={"total": float(total), "by_department": {str(d): float(a) for d, a in by_dept}},
        )
