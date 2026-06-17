from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.cfo.agent import CFOAgent
from app.agents.base import AgentContext
from app.agents.orchestrator import AgentOrchestrator
from app.agents.langgraph_orchestrator import run_langgraph_pipeline
from app.api.deps import get_company_id, get_current_user
from app.database.session import get_db
from app.models import User
from app.schemas.finance import CFOQueryRequest

router = APIRouter(prefix="/cfo", tags=["CFO Intelligence"])


@router.get("/analyze")
async def cfo_analyze(
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    cfo = CFOAgent(db)
    return await cfo.orchestrate(AgentContext(company_id=company_id))


@router.post("/ask")
async def cfo_ask(
    data: CFOQueryRequest,
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cfo = CFOAgent(db)
    return await cfo.answer_question(AgentContext(company_id=company_id, user_id=user.id), data.question)


@router.post("/orchestrate")
async def run_full_pipeline(
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    use_langgraph: bool = True,
):
    context = AgentContext(company_id=company_id, user_id=user.id)
    if use_langgraph:
        return await run_langgraph_pipeline(db, context)
    orchestrator = AgentOrchestrator(db)
    return await orchestrator.run_pipeline(company_id, user.id)
