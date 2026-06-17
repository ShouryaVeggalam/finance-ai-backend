# Celestra Finance AI Backend

**Your AI Finance Department** — an AI-powered Finance Operating System.

This is not accounting software. Celestra is a production-grade finance OS for managing money, cash flow, expenses, budgets, forecasts, risks, treasury, procurement, and executive financial intelligence.

## Tech Stack

- Python 3.12, FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic
- Redis, Celery (background workers + beat scheduler)
- JWT Authentication with RBAC
- LangGraph / LangChain + OpenAI-compatible models
- Docker, Prometheus, Grafana
- S3-compatible storage (MinIO)

## Quick Start

```bash
cd backend
cp .env.example .env
docker compose up -d
docker compose exec api python scripts/init_db.py
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs  
Grafana: http://localhost:3000  
Prometheus: http://localhost:9090  

## Architecture

### Finance AI Network (Agent Pipeline)

```
Transactions → Accounting → Expenses → Bank → Cash Flow → Revenue → Budget
→ Tax → Risk → Audit → Treasury → Procurement → Forecasting → CFO Agent
```

### Core Engines

| Engine | Purpose |
|--------|---------|
| Double Entry Ledger | Journal entries, trial balance, financial statements |
| Banking | Sync, reconciliation, fraud detection |
| Cash Flow | Runway, liquidity analysis |
| Financial Health | Composite health scoring |
| Treasury | Capital allocation, reserve management |
| Procurement | Vendor analysis, savings detection |
| Forecasting | Revenue/expense/cash scenarios |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/register` | Register company + founder |
| `POST /api/v1/auth/login` | JWT login |
| `POST /api/v1/auth/refresh` | Refresh tokens |
| `GET /api/v1/dashboard` | Executive dashboard |
| `GET /api/v1/accounting/*` | Accounting intelligence |
| `GET /api/v1/expenses/analyze` | Expense intelligence |
| `GET /api/v1/bank/analyze` | Bank intelligence |
| `GET /api/v1/cashflow/analyze` | Cash flow intelligence |
| `GET /api/v1/revenue/analyze` | Revenue intelligence |
| `GET /api/v1/budget/analyze` | Budget intelligence |
| `GET /api/v1/tax/analyze` | Tax intelligence |
| `GET /api/v1/risk/analyze` | Risk intelligence |
| `GET /api/v1/audit/analyze` | Audit intelligence |
| `GET /api/v1/treasury/analyze` | Treasury intelligence |
| `GET /api/v1/procurement/analyze` | Procurement intelligence |
| `GET /api/v1/forecasting/analyze` | Forecasting intelligence |
| `GET /api/v1/cfo/analyze` | CFO executive analysis |
| `POST /api/v1/cfo/ask` | Ask the AI CFO |
| `POST /api/v1/cfo/orchestrate` | Run full agent pipeline |
| `POST /api/v1/reports` | Generate financial reports |
| `WS /api/v1/ws/alerts/{company_id}` | Real-time alerts |

## RBAC Roles

Admin, Founder, Finance Manager, Accountant, Controller, CFO, Viewer

## Background Jobs

| Schedule | Job |
|----------|-----|
| Hourly | Cash flow refresh, risk refresh, forecast refresh, bank sync |
| Daily | Financial, budget, treasury summaries |
| Weekly | Executive finance report |
| Monthly | Board finance report |
| Quarterly | Strategic CFO report |

## Development

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info
```

## Project Structure

```
backend/
├── app/
│   ├── agents/          # 13 AI intelligence agents + orchestrator
│   ├── api/             # FastAPI routes and dependencies
│   ├── core/            # Config, security, logging, RBAC
│   ├── database/        # SQLAlchemy base and session
│   ├── events/          # Event-driven architecture bus
│   ├── integrations/    # ERP, banking, payment adapters
│   ├── models/          # 30+ domain models
│   ├── repositories/    # Repository pattern data access
│   ├── schemas/         # Pydantic v2 schemas
│   ├── services/        # Business logic + financial engines
│   ├── utils/           # S3 storage utilities
│   └── workers/         # Celery tasks and beat schedule
├── alembic/             # Database migrations
├── monitoring/          # Prometheus + Grafana config
├── scripts/             # DB initialization
└── tests/               # Unit and integration tests
```
