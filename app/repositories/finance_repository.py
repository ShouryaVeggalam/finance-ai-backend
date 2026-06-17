from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Expense,
    LedgerAccount,
    LedgerEntry,
    Transaction,
)
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Transaction)

    async def sum_by_type(
        self, company_id: UUID, transaction_type: str, start: date, end: date
    ) -> Decimal:
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.company_id == company_id,
            Transaction.transaction_type == transaction_type,
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
            Transaction.status == "posted",
        )
        result = await self.session.execute(stmt)
        return Decimal(str(result.scalar_one()))


class LedgerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_account_balance(self, ledger_account_id: UUID, company_id: UUID) -> Decimal:
        debit_stmt = select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.ledger_account_id == ledger_account_id,
            LedgerEntry.company_id == company_id,
            LedgerEntry.entry_type == "debit",
        )
        credit_stmt = select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.ledger_account_id == ledger_account_id,
            LedgerEntry.company_id == company_id,
            LedgerEntry.entry_type == "credit",
        )
        debit = Decimal(str((await self.session.execute(debit_stmt)).scalar_one()))
        credit = Decimal(str((await self.session.execute(credit_stmt)).scalar_one()))

        account = await self.session.get(LedgerAccount, ledger_account_id)
        if account and account.normal_balance == "credit":
            return credit - debit
        return debit - credit

    async def get_entries_by_journal(self, journal_id: UUID, company_id: UUID) -> list[LedgerEntry]:
        result = await self.session.execute(
            select(LedgerEntry).where(
                LedgerEntry.journal_id == journal_id,
                LedgerEntry.company_id == company_id,
            )
        )
        return list(result.scalars().all())


class ExpenseRepository(BaseRepository[Expense]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Expense)

    async def total_by_period(self, company_id: UUID, start: date, end: date) -> Decimal:
        stmt = select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.company_id == company_id,
            Expense.expense_date >= start,
            Expense.expense_date <= end,
            Expense.status.in_(["approved", "paid"]),
        )
        result = await self.session.execute(stmt)
        return Decimal(str(result.scalar_one()))

    async def by_department(
        self, company_id: UUID, start: date, end: date
    ) -> list[tuple[str | None, Decimal]]:
        stmt = (
            select(Expense.department, func.coalesce(func.sum(Expense.amount), 0))
            .where(
                Expense.company_id == company_id,
                Expense.expense_date >= start,
                Expense.expense_date <= end,
            )
            .group_by(Expense.department)
        )
        result = await self.session.execute(stmt)
        return [(row[0], Decimal(str(row[1]))) for row in result.all()]
