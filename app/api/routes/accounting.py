from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentOrchestrator
from app.api.deps import get_company_id, get_current_user
from app.database.session import get_db
from app.models import User
from app.schemas.finance import CFOQueryRequest, FinancialReportRequest, JournalEntryCreate
from app.services.ledger_engine import DoubleEntryLedgerEngine
from app.services.reporting_service import ReportingService

router = APIRouter(prefix="/accounting", tags=["Accounting Intelligence"])


@router.get("/statements")
async def financial_statements(
    period_start: date | None = None,
    period_end: date | None = None,
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    engine = DoubleEntryLedgerEngine(db)
    start = period_start or date.today().replace(day=1)
    end = period_end or date.today()
    return await engine.generate_financial_statements(company_id, start, end)


@router.get("/trial-balance")
async def trial_balance(
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    engine = DoubleEntryLedgerEngine(db)
    return await engine.get_trial_balance(company_id)


@router.post("/journal-entries")
async def post_journal(
    data: JournalEntryCreate,
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    engine = DoubleEntryLedgerEngine(db)
    lines = [line.model_dump() for line in data.lines]
    journal_id = await engine.post_journal(
        company_id, data.entry_date, data.description, lines
    )
    return {"journal_id": str(journal_id), "status": "posted"}


@router.get("/analyze")
async def analyze(
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    orchestrator = AgentOrchestrator(db)
    result = await orchestrator.run_single_agent("accounting", company_id)
    return result
