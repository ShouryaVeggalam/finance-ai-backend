from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    revenue: Decimal
    expenses: Decimal
    cash_position: Decimal
    runway_months: Decimal | None
    financial_health_score: Decimal | None
    budget_health_score: Decimal | None
    bank_health_score: Decimal | None
    treasury_health_score: Decimal | None
    procurement_health_score: Decimal | None
    risk_score: Decimal | None
    liquidity_position: Decimal
    capital_allocation: dict
    forecast_summary: dict
    top_insights: list[dict]
    cfo_recommendations: list[str]
    recent_activity: list[dict]
    generated_at: datetime


class HealthScoresResponse(BaseModel):
    overall: Decimal
    profitability: Decimal | None
    liquidity: Decimal | None
    growth: Decimal | None
    budget: Decimal | None
    risk: Decimal | None


class AgentAnalysisResponse(BaseModel):
    agent: str
    status: str
    score: Decimal | None = None
    insights: list[str] = []
    data: dict = {}
    generated_at: datetime
