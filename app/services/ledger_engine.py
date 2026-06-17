import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models import LedgerEntry
from app.repositories.finance_repository import LedgerRepository


class DoubleEntryLedgerEngine:
    """Double-entry bookkeeping engine with journal validation and balance tracking."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.ledger_repo = LedgerRepository(session)

    def validate_journal(self, lines: list[dict]) -> None:
        if len(lines) < 2:
            raise ValidationError("Journal entry requires at least two lines")
        total_debit = sum(
            Decimal(str(line["amount"])) for line in lines if line["entry_type"] == "debit"
        )
        total_credit = sum(
            Decimal(str(line["amount"])) for line in lines if line["entry_type"] == "credit"
        )
        if total_debit != total_credit:
            raise ValidationError(
                f"Debits ({total_debit}) must equal credits ({total_credit})"
            )

    async def post_journal(
        self,
        company_id: uuid.UUID,
        entry_date: date,
        description: str,
        lines: list[dict],
        transaction_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        self.validate_journal(lines)
        journal_id = uuid.uuid4()
        for line in lines:
            entry = LedgerEntry(
                company_id=company_id,
                journal_id=journal_id,
                ledger_account_id=line["ledger_account_id"],
                transaction_id=transaction_id,
                entry_type=line["entry_type"],
                amount=Decimal(str(line["amount"])),
                description=line.get("description") or description,
                entry_date=entry_date,
            )
            self.session.add(entry)
        await self.session.flush()
        return journal_id

    async def get_account_balance(
        self, ledger_account_id: uuid.UUID, company_id: uuid.UUID
    ) -> Decimal:
        return await self.ledger_repo.get_account_balance(ledger_account_id, company_id)

    async def get_trial_balance(self, company_id: uuid.UUID) -> list[dict]:
        from sqlalchemy import select

        from app.models import LedgerAccount

        accounts = await self.session.execute(
            select(LedgerAccount).where(
                LedgerAccount.company_id == company_id,
                LedgerAccount.is_active.is_(True),
            )
        )
        result = []
        for account in accounts.scalars().all():
            balance = await self.get_account_balance(account.id, company_id)
            result.append(
                {
                    "account_id": str(account.id),
                    "code": account.code,
                    "name": account.name,
                    "account_type": account.account_type,
                    "balance": float(balance),
                }
            )
        return result

    async def generate_financial_statements(
        self, company_id: uuid.UUID, period_start: date, period_end: date
    ) -> dict:
        trial = await self.get_trial_balance(company_id)
        assets = sum(r["balance"] for r in trial if r["account_type"] == "asset")
        liabilities = sum(r["balance"] for r in trial if r["account_type"] == "liability")
        equity = sum(r["balance"] for r in trial if r["account_type"] == "equity")
        revenue = sum(r["balance"] for r in trial if r["account_type"] == "revenue")
        expenses = sum(r["balance"] for r in trial if r["account_type"] == "expense")

        net_income = revenue - expenses
        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "profit_and_loss": {
                "revenue": revenue,
                "expenses": expenses,
                "net_income": net_income,
            },
            "balance_sheet": {
                "assets": assets,
                "liabilities": liabilities,
                "equity": equity + net_income,
                "total_liabilities_equity": liabilities + equity + net_income,
            },
            "cash_flow_statement": {
                "operating": net_income,
                "investing": 0,
                "financing": 0,
                "net_change": net_income,
            },
            "accounting_health_score": min(100, max(0, 100 - abs(assets - (liabilities + equity)))),
        }
