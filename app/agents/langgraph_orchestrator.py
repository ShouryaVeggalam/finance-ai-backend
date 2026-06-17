"""LangGraph-based Finance AI Network orchestration."""

from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.accounting.agent import AccountingAgent
from app.agents.audit.agent import AuditAgent
from app.agents.bank.agent import BankAgent
from app.agents.base import AgentContext, AgentResult
from app.agents.budget.agent import BudgetAgent
from app.agents.cashflow.agent import CashFlowAgent
from app.agents.cfo.agent import CFOAgent
from app.agents.expenses.agent import ExpenseAgent
from app.agents.forecasting.agent import ForecastingAgent
from app.agents.procurement.agent import ProcurementAgent
from app.agents.revenue.agent import RevenueAgent
from app.agents.risk.agent import RiskAgent
from app.agents.tax.agent import TaxAgent
from app.agents.treasury.agent import TreasuryAgent


class FinanceGraphState(TypedDict):
    context: AgentContext
    results: Annotated[list[AgentResult], lambda a, b: a + b]
    session: AsyncSession


def build_finance_graph(session: AsyncSession):
    """Build the Finance AI Network as a LangGraph state machine."""

    async def run_agent(agent_cls, state: FinanceGraphState) -> dict:
        agent = agent_cls(session)
        result = await agent.analyze(state["context"])
        state["context"].data[agent.name] = result.data
        return {"results": [result]}

    graph = StateGraph(FinanceGraphState)

    agents = [
        ("accounting", AccountingAgent),
        ("expenses", ExpenseAgent),
        ("bank", BankAgent),
        ("cashflow", CashFlowAgent),
        ("revenue", RevenueAgent),
        ("budget", BudgetAgent),
        ("tax", TaxAgent),
        ("risk", RiskAgent),
        ("audit", AuditAgent),
        ("treasury", TreasuryAgent),
        ("procurement", ProcurementAgent),
        ("forecasting", ForecastingAgent),
    ]

    for name, cls in agents:
        async def node(state, _cls=cls):
            return await run_agent(_cls, state)

        graph.add_node(name, node)

    async def cfo_node(state: FinanceGraphState) -> dict:
        cfo = CFOAgent(session)
        output = await cfo.orchestrate(state["context"])
        state["context"].data["cfo"] = output
        return {"results": []}

    graph.add_node("cfo", cfo_node)

    for i, (name, _) in enumerate(agents):
        next_node = agents[i + 1][0] if i + 1 < len(agents) else "cfo"
        graph.add_edge(name, next_node)

    graph.set_entry_point("accounting")
    graph.add_edge("cfo", END)

    return graph.compile()


async def run_langgraph_pipeline(session: AsyncSession, context: AgentContext) -> dict:
    graph = build_finance_graph(session)
    final_state = await graph.ainvoke(
        {"context": context, "results": [], "session": session}
    )
    return {
        "pipeline": "langgraph",
        "agent_results": [
            {"agent": r.agent, "score": float(r.score) if r.score else None, "insights": r.insights}
            for r in final_state["results"]
        ],
        "cfo": context.data.get("cfo"),
    }
