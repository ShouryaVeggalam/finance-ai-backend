import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BankAccount, BankTransaction, ReconciliationRecord
from app.repositories.domain_repository import BankAccountRepository, BankTransactionRepository


class BankingEngine:
    """Bank sync, reconciliation, fraud detection, and cash position validation."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.bank_repo = BankAccountRepository(session)
        self.tx_repo = BankTransactionRepository(session)

    async def get_verified_cash_position(self, company_id: uuid.UUID) -> Decimal:
        return await self.bank_repo.total_cash_position(company_id)

    async def sync_transactions(
        self,
        company_id: uuid.UUID,
        bank_account_id: uuid.UUID,
        transactions: list[dict],
    ) -> int:
        account = await self.bank_repo.get_by_id(bank_account_id, company_id)
        if not account:
            return 0
        synced = 0
        for tx in transactions:
            existing = await self.session.execute(
                select(BankTransaction).where(
                    BankTransaction.company_id == company_id,
                    BankTransaction.external_id == tx.get("external_id"),
                )
            )
            if existing.scalar_one_or_none():
                continue
            self.session.add(
                BankTransaction(
                    company_id=company_id,
                    bank_account_id=bank_account_id,
                    external_id=tx.get("external_id"),
                    amount=Decimal(str(tx["amount"])),
                    description=tx.get("description"),
                    transaction_date=tx["transaction_date"],
                    category=tx.get("category"),
                )
            )
            synced += 1
        account.last_synced_at = datetime.now(UTC)
        await self.session.flush()
        return synced

    async def detect_fraud_anomalies(self, company_id: uuid.UUID) -> list[dict]:
        result = await self.session.execute(
            select(BankTransaction).where(BankTransaction.company_id == company_id)
        )
        transactions = result.scalars().all()
        if not transactions:
            return []
        amounts = [abs(t.amount) for t in transactions]
        avg = sum(amounts) / len(amounts)
        threshold = avg * Decimal("5")
        anomalies = []
        for tx in transactions:
            if abs(tx.amount) > threshold:
                anomalies.append(
                    {
                        "transaction_id": str(tx.id),
                        "amount": float(tx.amount),
                        "description": tx.description,
                        "reason": "Amount exceeds 5x average transaction size",
                    }
                )
        return anomalies

    async def reconcile_account(
        self,
        company_id: uuid.UUID,
        bank_account_id: uuid.UUID,
        book_balance: Decimal,
        period_start: date,
        period_end: date,
    ) -> ReconciliationRecord:
        account = await self.bank_repo.get_by_id(bank_account_id, company_id)
        if not account:
            raise ValueError("Bank account not found")
        bank_balance = account.current_balance
        difference = book_balance - bank_balance
        record = ReconciliationRecord(
            company_id=company_id,
            bank_account_id=bank_account_id,
            period_start=period_start,
            period_end=period_end,
            book_balance=book_balance,
            bank_balance=bank_balance,
            difference=difference,
            status="reconciled" if difference == 0 else "discrepancy",
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def compute_bank_health_score(self, company_id: uuid.UUID) -> Decimal:
        accounts = await self.bank_repo.list_by_company(company_id)
        if not accounts:
            return Decimal("0")
        score = Decimal("100")
        now = datetime.now(UTC)
        for account in accounts:
            if account.last_synced_at:
                days_stale = (now - account.last_synced_at).days
                if days_stale > 7:
                    score -= Decimal("10")
            else:
                score -= Decimal("20")
        unreconciled = await self.session.execute(
            select(BankTransaction).where(
                BankTransaction.company_id == company_id,
                BankTransaction.is_reconciled.is_(False),
            )
        )
        unreconciled_count = len(list(unreconciled.scalars().all()))
        score -= min(Decimal("30"), Decimal(str(unreconciled_count)))
        return max(Decimal("0"), score)
