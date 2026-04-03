"""Tests for the in-memory credit ledger."""

import pytest
from mesh.core.ledger import Ledger, InsufficientFundsError, EscrowNotFoundError


class TestLedger:
    def test_init_balance(self, ledger):
        assert ledger.balance("buyer_001") == 10000

    def test_unknown_agent_balance_zero(self, ledger):
        assert ledger.balance("unknown") == 0.0

    def test_transfer_updates_balances(self, ledger):
        tx = ledger.transfer("buyer_001", "supplier_001", 1000, "payment", "o1")
        assert ledger.balance("buyer_001") == 9000
        assert ledger.balance("supplier_001") == 6000
        assert tx.amount == 1000

    def test_transfer_insufficient_funds_raises(self, ledger):
        with pytest.raises(InsufficientFundsError):
            ledger.transfer("buyer_001", "supplier_001", 99999)

    def test_transfer_negative_amount_raises(self, ledger):
        with pytest.raises(ValueError):
            ledger.transfer("buyer_001", "supplier_001", -100)

    def test_escrow_lock(self, ledger):
        record = ledger.escrow_lock("buyer_001", 5000, "order-1")
        assert ledger.balance("buyer_001") == 5000
        assert record.amount == 5000
        assert not record.released

    def test_escrow_lock_insufficient_funds(self, ledger):
        with pytest.raises(InsufficientFundsError):
            ledger.escrow_lock("buyer_001", 99999, "order-1")

    def test_escrow_release_distributes(self, ledger):
        ledger.escrow_lock("buyer_001", 6000, "order-1")
        txns = ledger.escrow_release("order-1", [
            ("supplier_001", 5000, "Payment"),
            ("inspector_001", 5, "Fee"),
            (Ledger.BURN_ADDRESS, 180, "Platform fee"),
        ])
        assert len(txns) >= 3
        assert ledger.balance("supplier_001") == 10000  # 5000 + 5000
        assert ledger.balance("inspector_001") == 2005

    def test_escrow_release_returns_remainder(self, ledger):
        ledger.escrow_lock("buyer_001", 6000, "order-1")
        txns = ledger.escrow_release("order-1", [
            ("supplier_001", 5000, "Payment"),
        ])
        # Remainder (1000) should go back to buyer
        assert ledger.balance("buyer_001") == 5000  # 10000 - 6000 + 1000

    def test_escrow_refund(self, ledger):
        ledger.escrow_lock("buyer_001", 3000, "order-1")
        assert ledger.balance("buyer_001") == 7000
        ledger.escrow_refund("order-1")
        assert ledger.balance("buyer_001") == 10000

    def test_double_release_raises(self, ledger):
        ledger.escrow_lock("buyer_001", 1000, "order-1")
        ledger.escrow_release("order-1", [("supplier_001", 900, "Pay")])
        with pytest.raises(EscrowNotFoundError):
            ledger.escrow_release("order-1", [("supplier_001", 100, "Pay")])

    def test_release_nonexistent_escrow_raises(self, ledger):
        with pytest.raises(EscrowNotFoundError):
            ledger.escrow_release("nonexistent", [])

    def test_transaction_count(self, ledger):
        assert ledger.transaction_count == 0
        ledger.transfer("buyer_001", "supplier_001", 100)
        assert ledger.transaction_count == 1

    def test_total_transacted(self, ledger):
        ledger.transfer("buyer_001", "supplier_001", 100)
        ledger.transfer("buyer_001", "logistics_001", 50)
        assert ledger.total_transacted() == 150

    def test_burn_address_doesnt_accumulate(self, ledger):
        ledger.transfer("buyer_001", Ledger.BURN_ADDRESS, 100, "burn")
        assert ledger.balance(Ledger.BURN_ADDRESS) == 0
