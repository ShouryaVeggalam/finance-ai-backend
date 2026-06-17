from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseSchema):
    reference: str
    description: str | None = None
    amount: Decimal = Field(gt=0)
    currency: str = "USD"
    transaction_type: str
    transaction_date: date
    category: str | None = None


class TransactionResponse(BaseSchema):
    id: UUID
    company_id: UUID
    reference: str
    amount: Decimal
    currency: str
    transaction_type: str
    status: str
    transaction_date: date
    category: str | None
    created_at: datetime


class JournalEntryLine(BaseSchema):
    ledger_account_id: UUID
    entry_type: str = Field(pattern="^(debit|credit)$")
    amount: Decimal = Field(gt=0)
    description: str | None = None


class JournalEntryCreate(BaseSchema):
    entry_date: date
    description: str
    lines: list[JournalEntryLine] = Field(min_length=2)


class LedgerAccountResponse(BaseSchema):
    id: UUID
    name: str
    code: str
    account_type: str
    normal_balance: str


class ExpenseCreate(BaseSchema):
    amount: Decimal = Field(gt=0)
    category: str | None = None
    department: str | None = None
    expense_date: date
    description: str | None = None
    vendor_id: UUID | None = None


class ExpenseResponse(BaseSchema):
    id: UUID
    amount: Decimal
    category: str | None
    department: str | None
    status: str
    expense_date: date
    description: str | None


class BudgetCreate(BaseSchema):
    name: str
    department: str | None = None
    period_type: str = "monthly"
    period_start: date
    period_end: date
    allocated_amount: Decimal = Field(gt=0)
    category: str | None = None


class BudgetResponse(BaseSchema):
    id: UUID
    name: str
    department: str | None
    allocated_amount: Decimal
    spent_amount: Decimal
    period_start: date
    period_end: date


class BankAccountResponse(BaseSchema):
    id: UUID
    name: str
    institution: str | None
    current_balance: Decimal
    available_balance: Decimal
    currency: str
    last_synced_at: datetime | None


class FinancialReportRequest(BaseSchema):
    report_type: str
    period_start: date | None = None
    period_end: date | None = None


class CFOQueryRequest(BaseSchema):
    question: str = Field(min_length=5, max_length=2000)


class ScenarioCreate(BaseSchema):
    name: str
    scenario_type: str
    parameters: dict


class PurchaseRequestCreate(BaseSchema):
    title: str
    amount: Decimal = Field(gt=0)
    vendor_id: UUID | None = None
    justification: str | None = None


class NotificationResponse(BaseSchema):
    id: UUID
    title: str
    message: str
    alert_type: str
    severity: str
    is_read: bool
    created_at: datetime


class FinancialInsightResponse(BaseSchema):
    id: UUID
    insight_type: str
    title: str
    summary: str
    severity: str
    agent_source: str | None
    created_at: datetime
