from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_id, get_current_user
from app.database.session import get_db
from app.models import Expense, User
from app.repositories.finance_repository import ExpenseRepository
from app.schemas.finance import ExpenseCreate, ExpenseResponse, FinancialReportRequest
from app.services.reporting_service import ReportingService

router = APIRouter(tags=["Finance Operations"])


@router.post("/expenses", response_model=ExpenseResponse, tags=["Expense Intelligence"])
async def create_expense(
    data: ExpenseCreate,
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    expense = Expense(
        company_id=company_id,
        submitted_by=user.id,
        **data.model_dump(),
    )
    repo = ExpenseRepository(db)
    return await repo.create(expense)


@router.get("/expenses", response_model=list[ExpenseResponse], tags=["Expense Intelligence"])
async def list_expenses(
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    repo = ExpenseRepository(db)
    return list(await repo.list_by_company(company_id))


@router.post("/reports", tags=["Reporting"])
async def generate_report(
    data: FinancialReportRequest,
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    service = ReportingService(db)
    report = await service.generate_report(
        company_id, data.report_type, data.period_start, data.period_end
    )
    return {
        "id": str(report.id),
        "report_type": report.report_type,
        "title": report.title,
        "content": report.content_json,
        "generated_at": report.created_at.isoformat(),
    }


@router.get("/reports", tags=["Reporting"])
async def list_reports(
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    from app.models import FinancialReport

    result = await db.execute(
        select(FinancialReport)
        .where(FinancialReport.company_id == company_id)
        .order_by(FinancialReport.created_at.desc())
        .limit(50)
    )
    reports = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "report_type": r.report_type,
            "title": r.title,
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]
