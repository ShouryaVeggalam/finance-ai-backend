from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "celestra_finance",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.jobs"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "hourly-cashflow-refresh": {
        "task": "app.workers.jobs.refresh_cashflow",
        "schedule": crontab(minute=0),
    },
    "hourly-risk-refresh": {
        "task": "app.workers.jobs.refresh_risk",
        "schedule": crontab(minute=15),
    },
    "hourly-forecast-refresh": {
        "task": "app.workers.jobs.refresh_forecast",
        "schedule": crontab(minute=30),
    },
    "hourly-bank-sync": {
        "task": "app.workers.jobs.sync_banks",
        "schedule": crontab(minute=45),
    },
    "daily-financial-summary": {
        "task": "app.workers.jobs.daily_financial_summary",
        "schedule": crontab(hour=6, minute=0),
    },
    "daily-budget-summary": {
        "task": "app.workers.jobs.daily_budget_summary",
        "schedule": crontab(hour=6, minute=30),
    },
    "daily-treasury-summary": {
        "task": "app.workers.jobs.daily_treasury_summary",
        "schedule": crontab(hour=7, minute=0),
    },
    "weekly-executive-report": {
        "task": "app.workers.jobs.weekly_executive_report",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
    },
    "monthly-board-report": {
        "task": "app.workers.jobs.monthly_board_report",
        "schedule": crontab(hour=9, minute=0, day_of_month=1),
    },
    "quarterly-cfo-report": {
        "task": "app.workers.jobs.quarterly_cfo_report",
        "schedule": crontab(hour=10, minute=0, day_of_month=1, month_of_year="1,4,7,10"),
    },
}
