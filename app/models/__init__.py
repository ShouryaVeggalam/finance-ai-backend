import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TenantMixin, TimestampMixin, UUIDMixin


class AccountType(StrEnum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    POSTED = "posted"
    RECONCILED = "reconciled"
    VOID = "void"


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class ExpenseStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class BudgetPeriod(StrEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Company(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    fiscal_year_start_month: Mapped[int] = mapped_column(default=1)
    settings_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    users: Mapped[list["User"]] = relationship(back_populates="company")
    accounts: Mapped[list["Account"]] = relationship(back_populates="company")


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company: Mapped["Company"] = relationship(back_populates="users")


class Account(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "accounts"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    company: Mapped["Company"] = relationship(back_populates="accounts")

    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_account_company_code"),)


class LedgerAccount(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "ledger_accounts"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    normal_balance: Mapped[str] = mapped_column(String(10), default="debit")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class LedgerEntry(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "ledger_entries"

    journal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    ledger_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledger_accounts.id"), nullable=False
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    entry_type: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)


class Transaction(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "transactions"

    reference: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=TransactionStatus.PENDING)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class Invoice(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "invoices"

    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(20), default=InvoiceStatus.DRAFT)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    line_items: Mapped[dict | None] = mapped_column(JSONB, default=list)


class Expense(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "expenses"

    vendor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("vendors.id"))
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    category: Mapped[str | None] = mapped_column(String(100))
    department: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default=ExpenseStatus.DRAFT)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    receipt_url: Mapped[str | None] = mapped_column(String(500))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class Vendor(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "vendors"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(100))
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    total_spend: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class Customer(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    mrr: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    arr: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    segment: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class Budget(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "budgets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100))
    period_type: Mapped[str] = mapped_column(String(20), default=BudgetPeriod.MONTHLY)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    spent_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    category: Mapped[str | None] = mapped_column(String(100))


class Forecast(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "forecasts"

    forecast_type: Mapped[str] = mapped_column(String(50), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    assumptions: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    scenario: Mapped[str] = mapped_column(String(50), default="base")


class CashFlow(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "cash_flows"

    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    closing_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    inflows: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    outflows: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    net_cash_flow: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))


class TaxRecord(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "tax_records"

    tax_type: Mapped[str] = mapped_column(String(50), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    liability_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))


class RiskRecord(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "risk_records"

    risk_type: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default=RiskLevel.MEDIUM)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    mitigation: Mapped[str | None] = mapped_column(Text)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_at: Mapped[datetime] = mapped_column(nullable=False)


class AuditRecord(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "audit_records"

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    changes: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45))


class FinancialInsight(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "financial_insights"

    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    agent_source: Mapped[str | None] = mapped_column(String(50))
    data_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class FinancialReport(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "financial_reports"

    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    content_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(500))
    generated_by: Mapped[str | None] = mapped_column(String(50))


class Notification(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class ActivityLog(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "activity_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(100))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    details: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class BankAccount(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "bank_accounts"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution: Mapped[str | None] = mapped_column(String(255))
    account_number_masked: Mapped[str | None] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    current_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    available_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    last_synced_at: Mapped[datetime | None] = mapped_column()
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    external_id: Mapped[str | None] = mapped_column(String(255))


class BankTransaction(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "bank_transactions"

    bank_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False)
    category: Mapped[str | None] = mapped_column(String(100))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class ReconciliationRecord(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "reconciliation_records"

    bank_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    book_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    bank_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    difference: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    notes: Mapped[str | None] = mapped_column(Text)


class TreasuryPosition(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "treasury_positions"

    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_cash: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_investments: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    total_debt: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    net_position: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    reserve_ratio: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class LiquidityForecast(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "liquidity_forecasts"

    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    projected_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    minimum_required: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    surplus_deficit: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))


class CapitalAllocation(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "capital_allocations"

    category: Mapped[str] = mapped_column(String(100), nullable=False)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    utilized_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class VendorContract(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "vendor_contracts"

    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False
    )
    contract_number: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    terms: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class PurchaseRequest(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "purchase_requests"

    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("vendors.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=ApprovalStatus.PENDING)
    justification: Mapped[str | None] = mapped_column(Text)


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "purchase_orders"

    purchase_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_requests.id")
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False
    )
    po_number: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    order_date: Mapped[date] = mapped_column(Date, nullable=False)


class ProcurementApproval(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "procurement_approvals"

    purchase_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_requests.id"), nullable=False
    )
    approver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default=ApprovalStatus.PENDING)
    comments: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column()


class FinancialHealthScore(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "financial_health_scores"

    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    overall_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    profitability_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    liquidity_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    growth_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    budget_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    breakdown: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class RunwayForecast(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "runway_forecasts"

    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    monthly_burn: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    runway_months: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    zero_cash_date: Mapped[date | None] = mapped_column(Date)
    assumptions: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class ScenarioModel(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "scenario_models"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False)
    results: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
