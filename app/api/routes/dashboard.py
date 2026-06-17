from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentOrchestrator
from app.api.deps import get_company_id, get_current_user
from app.database.session import get_db
from app.models import User
from app.schemas.dashboard import AgentAnalysisResponse, DashboardResponse
from app.schemas.finance import CFOQueryRequest
from app.services.dashboard_service import DashboardService

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = DashboardService(db)
    return await service.get_dashboard(company_id)
