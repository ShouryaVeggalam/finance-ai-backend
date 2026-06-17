from decimal import Decimal

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.services.ledger_engine import DoubleEntryLedgerEngine


class AccountingAgent(BaseAgent):
    name = "accounting"
    description = "Financial record management, journal entries, and financial statements"

    async def analyze(self, context: AgentContext) -> AgentResult:
        engine = DoubleEntryLedgerEngine(self.session)
        from datetime import date, timedelta

        end = date.today()
        start = end - timedelta(days=30)
        statements = await engine.generate_financial_statements(context.company_id, start, end)
        score = Decimal(str(statements.get("accounting_health_score", 75)))
        insights = [
            f"Net income: ${statements['profit_and_loss']['net_income']:,.2f}",
            f"Total assets: ${statements['balance_sheet']['assets']:,.2f}",
        ]
        llm = await self._llm_analyze(
            "You are an accounting intelligence agent for a finance OS.",
            f"Summarize accounting health: {statements}",
        )
        insights.append(llm)
        return AgentResult(agent=self.name, score=score, insights=insights, data=statements)
