"""Integration tests for the economic settlement pipeline."""

import pytest
from mesh.core.ledger import Ledger, InsufficientFundsError, EscrowNotFoundError
from mesh.core.reputation import ReputationEngine
from mesh.negotiation.arbiter import Arbiter


class TestMultiOrderSettlement:
    """Test multiple orders running through settlement concurrently."""

    @pytest.fixture
    def system(self):
        ledger = Ledger()
        reputation = ReputationEngine()
        # Initialize participants
        for agent_id, balance in [
            ("buyer_001", 50000),
            ("supplier_a", 10000),
            ("supplier_b", 10000),
            ("logistics_001", 5000),
            ("inspector_001", 5000),
        ]:
            ledger.init_balance(agent_id, balance)
            role = agent_id.split("_")[0]
            if role == "supplier":
                reputation.register(agent_id, "supplier", ["electronics"])
            else:
                reputation.register(agent_id, role, [])
        return ledger, reputation

    def test_three_orders_settle_sequentially(self, system):
        ledger, reputation = system
        orders = [
            {"id": "order_001", "amount": 5000, "supplier": "supplier_a", "quality": 0.92},
            {"id": "order_002", "amount": 3000, "supplier": "supplier_b", "quality": 0.88},
            {"id": "order_003", "amount": 4000, "supplier": "supplier_a", "quality": 0.95},
        ]

        for order in orders:
            escrow = order["amount"] + 20
            ledger.escrow_lock("buyer_001", escrow, order["id"])
            supplier_pay = order["amount"] * 0.92
            inspector_fee = 5.0
            burn = order["amount"] * 0.03
            ledger.escrow_release(order["id"], [
                (order["supplier"], supplier_pay, "Fulfillment"),
                ("inspector_001", inspector_fee, "Inspection"),
                (ledger.BURN_ADDRESS, burn, "Burn"),
            ])
            reputation.record_success(
                order["supplier"], "electronics",
                quality_score=order["quality"], order_id=order["id"],
            )

        # Verify balances shifted correctly
        assert ledger.balance("supplier_a") > 10000
        assert ledger.balance("supplier_b") > 10000
        assert ledger.balance("buyer_001") < 50000
        assert ledger.transaction_count > 0

    def test_mixed_success_and_failure(self, system):
        ledger, reputation = system
        # Order 1: Success
        ledger.escrow_lock("buyer_001", 5020, "order_ok")
        ledger.escrow_release("order_ok", [
            ("supplier_a", 4600, "Payment"),
            ("inspector_001", 5.0, "Fee"),
            (ledger.BURN_ADDRESS, 150, "Burn"),
        ])
        reputation.record_success("supplier_a", "electronics", quality_score=0.93)

        # Order 2: Failure — refund
        ledger.escrow_lock("buyer_001", 3020, "order_fail")
        ledger.escrow_refund("order_fail")
        reputation.record_failure("supplier_b", "electronics", "quality_fail", "order_fail")

        # Supplier A should have better reputation
        score_a = reputation.get_score("supplier_a", "electronics")
        score_b = reputation.get_score("supplier_b", "electronics")
        assert score_a > score_b

    def test_ledger_invariant_total_preserved(self, system):
        """Total money in system (including escrow) should be conserved minus burns."""
        ledger, _ = system
        initial_total = sum(ledger.balance(a) for a in ["buyer_001", "supplier_a", "supplier_b", "logistics_001", "inspector_001"])

        ledger.escrow_lock("buyer_001", 5000, "order_inv")
        during_escrow = sum(ledger.balance(a) for a in ["buyer_001", "supplier_a", "supplier_b", "logistics_001", "inspector_001"])
        assert during_escrow == initial_total - 5000  # 5000 is in escrow

        burn_amount = 100
        ledger.escrow_release("order_inv", [
            ("supplier_a", 4500, "Pay"),
            (ledger.BURN_ADDRESS, burn_amount, "Burn"),
        ])
        # After release: money returns minus burn
        after_total = sum(ledger.balance(a) for a in ["buyer_001", "supplier_a", "supplier_b", "logistics_001", "inspector_001"])
        assert after_total == initial_total - burn_amount


class TestDisputeResolution:
    """Test the arbiter's dispute resolution logic."""

    @pytest.fixture
    def arbiter(self):
        ledger = Ledger()
        reputation = ReputationEngine()
        reputation.register("supplier_001", "supplier", ["electronics"])
        reputation.register("logistics_001", "logistics", ["shipping"])
        return Arbiter(ledger, reputation)

    def test_quality_dispute_high_severity(self, arbiter):
        result = arbiter.resolve_quality_dispute(
            order_id="order_001", supplier_id="supplier_001",
            capability="electronics", quality_score=0.3,
            quality_threshold=0.85, quantity_expected=100, quantity_defective=40,
        )
        assert result.outcome == "full_refund"
        assert result.refund_percentage == 1.0
        assert result.supplier_penalty < 0

    def test_quality_dispute_moderate(self, arbiter):
        result = arbiter.resolve_quality_dispute(
            order_id="order_002", supplier_id="supplier_001",
            capability="electronics", quality_score=0.7,
            quality_threshold=0.85, quantity_expected=100, quantity_defective=15,
        )
        assert result.outcome in ("partial_refund", "full_refund")

    def test_quality_dispute_borderline_pass(self, arbiter):
        result = arbiter.resolve_quality_dispute(
            order_id="order_003", supplier_id="supplier_001",
            capability="electronics", quality_score=0.86,
            quality_threshold=0.85, quantity_expected=100, quantity_defective=2,
        )
        assert result.outcome == "accepted"
        assert result.refund_percentage == 0.0

    def test_late_delivery_penalty(self, arbiter):
        penalty_pct = arbiter.resolve_late_delivery(
            order_id="order_004", supplier_id="supplier_001",
            logistics_id="logistics_001", capability="electronics",
            seconds_late=120, deadline_seconds=60,
        )
        assert penalty_pct > 0

    def test_no_show_resolution(self, arbiter):
        # resolve_no_show returns None, just penalizes reputation
        arbiter.resolve_no_show(
            order_id="order_005", agent_id="supplier_001", capability="electronics",
        )
