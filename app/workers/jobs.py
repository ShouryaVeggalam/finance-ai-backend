import asyncio
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.agents.orchestrator import AgentOrchestrator
from app.core.config import settings
from app.core.logging import get_logger
from app.models import Company, Notification
from app.services.cashflow_engine import CashFlowEngine
from app.services.forecasting_engine import ForecastingEngine
from app.services.health_engine import FinancialHealthEngine
from app.services.reporting_service import ReportingService
from app.services.treasury_engine import TreasuryEngine
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


def _get_session_factory():
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _get_all_companies(session: AsyncSession) -> list[UUID]:
    result = await session.execute(select(Company.id).where(Company.is_active.is_(True)))
    return [row[0] for row in result.all()]


async def _create_alert(session: AsyncSession, company_id: UUID, title: str, message: str, alert_type: str):
    notification = Notification(
        company_id=company_id,
        title=title,
        message=message,
        alert_type=alert_type,
        severity="warning",
    )
    session.add(notification)
    await session.commit()


@celery_app.task(name="app.workers.jobs.refresh_cashflow")
def refresh_cashflow():
    async def _run():
        factory = _get_session_factory()
        async with factory() as session:
            for company_id in await _get_all_companies(session):
                engine = CashFlowEngine(session)
                analysis = await engine.analyze_liquidity(company_id)
                if analysis["runway_months"] < 6:
                    await _create_alert(
                        session,
                        company_id,
                        "Low Cash Runway",
                        f"Runway is {analysis['runway_months']:.1f} months",
                        "liquidity_alert",
                    )
                await session.commit()
        logger.info("cashflow_refresh_complete")

    run_async(_run())


@celery_app.task(name="app.workers.jobs.refresh_risk")
def refresh_risk():
    async def _run():
        factory = _get_session_factory()
        async with factory() as session:
            orchestrator = AgentOrchestrator(session)
            for company_id in await _get_all_companies(session):
                await orchestrator.run_single_agent("risk", company_id)
                await session.commit()
        logger.info("risk_refresh_complete")

    run_async(_run())


@celery_app.task(name="app.workers.jobs.refresh_forecast")
def refresh_forecast():
    async def _run():
        factory = _get_session_factory()
        async with factory() as session:
            engine = ForecastingEngine(session)
            for company_id in await _get_all_companies(session):
                await engine.forecast_cash(company_id, 6)
                await session.commit()
        logger.info("forecast_refresh_complete")

    run_async(_run())


@celery_app.task(name="app.workers.jobs.sync_banks")
def sync_banks():
    logger.info("bank_sync_complete")


@celery_app.task(name="app.workers.jobs.daily_financial_summary")
def daily_financial_summary():
    async def _run():
        factory = _get_session_factory()
        async with factory() as session:
            health = FinancialHealthEngine(session)
            for company_id in await _get_all_companies(session):
                await health.compute_health_score(company_id)
                await session.commit()
        logger.info("daily_financial_summary_complete")

    run_async(_run())


@celery_app.task(name="app.workers.jobs.daily_budget_summary")
def daily_budget_summary():
    async def _run():
        factory = _get_session_factory()
        async with factory() as session:
            health = FinancialHealthEngine(session)
            for company_id in await _get_all_companies(session):
                score = await health.budget_health_score(company_id)
                if score < 70:
                    await _create_alert(
                        session,
                        company_id,
                        "Budget Alert",
                        f"Budget health score dropped to {float(score):.0f}",
                        "budget_alert",
                    )
                await session.commit()
        logger.info("daily_budget_summary_complete")

    run_async(_run())


@celery_app.task(name="app.workers.jobs.daily_treasury_summary")
def daily_treasury_summary():
    async def _run():
        factory = _get_session_factory()
        async with factory() as session:
            treasury = TreasuryEngine(session)
            for company_id in await _get_all_companies(session):
                await treasury.get_treasury_position(company_id)
                await session.commit()
        logger.info("daily_treasury_summary_complete")

    run_async(_run())


@celery_app.task(name="app.workers.jobs.weekly_executive_report")
def weekly_executive_report():
    async def _run():
        factory = _get_session_factory()
        async with factory() as session:
            reporting = ReportingService(session)
            for company_id in await _get_all_companies(session):
                await reporting.generate_report(company_id, "executive_cfo")
                await session.commit()
        logger.info("weekly_executive_report_complete")

    run_async(_run())


@celery_app.task(name="app.workers.jobs.monthly_board_report")
def monthly_board_report():
    async def _run():
        factory = _get_session_factory()
        async with factory() as session:
            reporting = ReportingService(session)
            for company_id in await _get_all_companies(session):
                await reporting.generate_report(company_id, "board")
                await session.commit()
        logger.info("monthly_board_report_complete")

    run_async(_run())


@celery_app.task(name="app.workers.jobs.quarterly_cfo_report")
def quarterly_cfo_report():
    async def _run():
        factory = _get_session_factory()
        async with factory() as session:
            orchestrator = AgentOrchestrator(session)
            for company_id in await _get_all_companies(session):
                await orchestrator.run_pipeline(company_id)
                await session.commit()
        logger.info("quarterly_cfo_report_complete")

    run_async(_run())
