import pytest
from decimal import Decimal

from app.services.ledger_engine import DoubleEntryLedgerEngine


class TestDoubleEntryLedgerEngine:
    def test_validate_journal_requires_balance(self):
        engine = DoubleEntryLedgerEngine(None)  # type: ignore[arg-type]
        lines = [
            {"entry_type": "debit", "amount": Decimal("100")},
            {"entry_type": "credit", "amount": Decimal("50")},
        ]
        with pytest.raises(Exception) as exc:
            engine.validate_journal(lines)
        assert "must equal" in str(exc.value)

    def test_validate_journal_passes_balanced_entries(self):
        engine = DoubleEntryLedgerEngine(None)  # type: ignore[arg-type]
        lines = [
            {"entry_type": "debit", "amount": Decimal("100")},
            {"entry_type": "credit", "amount": Decimal("100")},
        ]
        engine.validate_journal(lines)

    def test_validate_journal_requires_minimum_lines(self):
        engine = DoubleEntryLedgerEngine(None)  # type: ignore[arg-type]
        with pytest.raises(Exception):
            engine.validate_journal([{"entry_type": "debit", "amount": Decimal("100")}])
