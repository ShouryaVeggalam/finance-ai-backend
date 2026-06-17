from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_id, get_current_user
from app.database.session import get_db
from app.models import Notification, User
from app.repositories.domain_repository import NotificationRepository
from app.schemas.finance import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications & Alerts"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    repo = NotificationRepository(db)
    notifications = await repo.list_by_company(company_id)
    return list(notifications)


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: UUID,
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    repo = NotificationRepository(db)
    notification = await repo.get_by_id(notification_id, company_id)
    if notification:
        notification.is_read = True
        await repo.update(notification)
    return {"status": "ok"}
