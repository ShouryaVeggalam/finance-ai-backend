"""Agent route factory for finance intelligence endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentOrchestrator
from app.api.deps import get_company_id, get_current_user
from app.database.session import get_db
from app.models import User


def create_agent_router(prefix: str, agent_name: str, tag: str) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("/analyze")
    async def analyze(
        company_id: UUID = Depends(get_company_id),
        db: AsyncSession = Depends(get_db),
        _user: User = Depends(get_current_user),
    ):
        orchestrator = AgentOrchestrator(db)
        return await orchestrator.run_single_agent(agent_name, company_id)

    return router
