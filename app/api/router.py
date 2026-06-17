from fastapi import APIRouter

from app.api.routes.accounting import router as accounting_router
from app.api.routes.agents import create_agent_router
from app.api.routes.auth import router as auth_router
from app.api.routes.cfo import router as cfo_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.finance import router as finance_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.websocket import router as ws_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(accounting_router)
api_router.include_router(finance_router)
api_router.include_router(cfo_router)
api_router.include_router(notifications_router)
api_router.include_router(ws_router)

AGENT_ROUTES = [
    ("/expenses", "expenses", "Expense Intelligence"),
    ("/bank", "bank", "Bank Intelligence"),
    ("/cashflow", "cashflow", "Cash Flow Intelligence"),
    ("/revenue", "revenue", "Revenue Intelligence"),
    ("/budget", "budget", "Budget Intelligence"),
    ("/tax", "tax", "Tax Intelligence"),
    ("/risk", "risk", "Risk Intelligence"),
    ("/audit", "audit", "Audit Intelligence"),
    ("/treasury", "treasury", "Treasury Intelligence"),
    ("/procurement", "procurement", "Procurement Intelligence"),
    ("/forecasting", "forecasting", "Forecasting Intelligence"),
]

for prefix, agent, tag in AGENT_ROUTES:
    api_router.include_router(create_agent_router(prefix, agent, tag))
