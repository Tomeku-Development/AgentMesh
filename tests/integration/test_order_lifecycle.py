"""Integration tests for the full order lifecycle (offline — no broker needed)."""

import pytest
from mesh.core.messages import (
    PurchaseOrderRequest,
    SupplierBid,
    CounterOffer,
    BidAcceptance,
    InspectionReport,
    OrderStatus,
)
from mesh.core.ledger import Ledger, InsufficientFundsError
from mesh.core.reputation import ReputationEngine
from mesh.negotiation.engine import NegotiationEngine


class TestOrderNegotiationPipeline:
    """End-to-end negotiation without a broker."""

    @pytest.fixture
    def engine(self):
        return NegotiationEngine()

    @pytest.fixture
    def ledger(self):
        ld = Ledger()
        ld.init_balance("buyer_001", 10000)
        ld.init_balance("supplier_a", 5000)
        ld.init_balance("supplier_b", 5000)
        ld.init_balance("logistics_001", 2000)
        ld.init_balance("inspector_001", 2000)
        return ld

    @pytest.fixture
    def reputation(self):
        engine = ReputationEngine()
        engine.register("buyer_001", "buyer", ["electronics"])
        engine.register("supplier_a", "supplier", ["electronics"])
        engine.register("supplier_b", "supplier", ["electronics"])
        engine.register("logistics_001", "logistics", ["shipping"])
        engine.register("inspector_001", "inspector", ["quality_control"])
        return engine

    def test_bid_evaluation_selects_best_price(self, engine, reputation):
        session = engine.create_session(
            order_id="order_001", buyer_id="buyer_001",
            max_price=120, market_price=100, quality_threshold=0.85,
            bid_window=30, negotiate_window=30,
        )

        bid_a = SupplierBid(
            order_id="order_001", supplier_id="supplier_a",
            price_per_unit=95, available_quantity=50,
            estimated_fulfillment_seconds=10, reputation_score=0.7,
        )
        bid_b = SupplierBid(
            order_id="order_001", supplier_id="supplier_b",
            price_per_unit=105, available_quantity=50,
            estimated_fulfillment_seconds=8, reputation_score=0.6,
        )
        session.add_bid(bid_a)
        session.add_bid(bid_b)

        def score_fn(bid):
            return reputation.score_bid(
                price=bid.price_per_unit, max_price=120,
                reputation=bid.reputation_score,
                estimated_time=bid.estimated_fulfillment_seconds,
                deadline=60, confidence=0.5,
            )

        best, should_counter = engine.evaluate_bids("order_001", score_fn)
        assert best is not None
        # Supplier A has the lower price, should score higher
        assert best.supplier_id == "supplier_a"

    def test_counter_offer_round_tracking(self, engine):
        engine.create_session(
            order_id="order_001", buyer_id="buyer_001",
            max_price=120, market_price=100, quality_threshold=0.85,
            bid_window=30, negotiate_window=30,
        )
        bid = SupplierBid(
            order_id="order_001", supplier_id="supplier_a",
            price_per_unit=115, available_quantity=50,
            estimated_fulfillment_seconds=10,
        )
        session = engine.get_session("order_001")
        session.add_bid(bid)

        # Must evaluate bids to transition state to EVALUATING before counter
        engine.evaluate_bids("order_001")

        counter = engine.generate_counter("order_001", bid)
        assert counter is not None
        assert counter.proposed_price_per_unit < bid.price_per_unit
        assert session.current_round == 1  # One round recorded

    def test_max_rounds_prevents_infinite_negotiation(self, engine):
        engine.create_session(
            order_id="order_001", buyer_id="buyer_001",
            max_price=120, market_price=100, quality_threshold=0.85,
            bid_window=30, negotiate_window=30, max_rounds=2,
        )
        session = engine.get_session("order_001")
        bid = SupplierBid(
            order_id="order_001", supplier_id="supplier_a",
            price_per_unit=115, available_quantity=50,
            estimated_fulfillment_seconds=10,
        )
        session.add_bid(bid)

        # Round 1 → 2
        engine.generate_counter("order_001", bid)
        # Round 2 → should not allow more
        assert not session.can_counter

    def test_accept_bid_sets_winner(self, engine):
        engine.create_session(
            order_id="order_001", buyer_id="buyer_001",
            max_price=120, market_price=100, quality_threshold=0.85,
            bid_window=30, negotiate_window=30,
        )
        bid = SupplierBid(
            order_id="order_001", supplier_id="supplier_a",
            price_per_unit=95, available_quantity=50,
            estimated_fulfillment_seconds=10,
        )
        session = engine.get_session("order_001")
        session.add_bid(bid)
        engine.accept_bid("order_001", bid)
        assert session.winner_supplier_id == "supplier_a"
        assert session.agreed_price == 95


class TestEscrowSettlementPipeline:
    """Test escrow lock, release, and refund flows."""

    @pytest.fixture
    def ledger(self):
        ld = Ledger()
        ld.init_balance("buyer_001", 10000)
        ld.init_balance("supplier_a", 5000)
        ld.init_balance("logistics_001", 2000)
        ld.init_balance("inspector_001", 2000)
        return ld

    def test_full_settlement_flow(self, ledger):
        # 1. Lock escrow
        agreed_total = 95 * 50  # 4750
        escrow_amount = agreed_total + 20  # buffer for fees
        ledger.escrow_lock("buyer_001", escrow_amount, "order_001")
        assert ledger.balance("buyer_001") == 10000 - escrow_amount

        # 2. Release to participants
        supplier_payment = agreed_total * 0.92
        inspector_fee = 5.0
        burn = agreed_total * 0.03
        ledger.escrow_release("order_001", [
            ("supplier_a", supplier_payment, "Fulfillment"),
            ("inspector_001", inspector_fee, "Inspection fee"),
            (ledger.BURN_ADDRESS, burn, "Platform fee"),
        ])

        assert ledger.balance("supplier_a") == 5000 + supplier_payment
        assert ledger.balance("inspector_001") == 2000 + inspector_fee
        assert ledger.balance("buyer_001") > 10000 - escrow_amount  # Remainder returned

    def test_escrow_refund_on_inspection_fail(self, ledger):
        escrow_amount = 4770
        ledger.escrow_lock("buyer_001", escrow_amount, "order_002")
        buyer_after_lock = ledger.balance("buyer_001")

        ledger.escrow_refund("order_002")
        assert ledger.balance("buyer_001") == buyer_after_lock + escrow_amount

    def test_double_release_raises(self, ledger):
        ledger.escrow_lock("buyer_001", 1000, "order_003")
        ledger.escrow_release("order_003", [("supplier_a", 900, "Payment")])
        with pytest.raises(Exception):
            ledger.escrow_release("order_003", [("supplier_a", 100, "Extra")])

    def test_insufficient_funds_for_escrow(self, ledger):
        with pytest.raises(InsufficientFundsError):
            ledger.escrow_lock("buyer_001", 20000, "order_004")

    def test_multiple_concurrent_escrows(self, ledger):
        ledger.escrow_lock("buyer_001", 3000, "order_a")
        ledger.escrow_lock("buyer_001", 3000, "order_b")
        assert ledger.balance("buyer_001") == 10000 - 6000

        ledger.escrow_release("order_a", [("supplier_a", 2800, "Payment")])
        ledger.escrow_refund("order_b")
        # buyer gets remainder from order_a + full refund from order_b
        assert ledger.balance("buyer_001") == 10000 - 6000 + 200 + 3000


class TestReputationIntegration:
    """Test reputation across multiple transactions."""

    @pytest.fixture
    def reputation(self):
        engine = ReputationEngine()
        engine.register("supplier_a", "supplier", ["electronics"])
        engine.register("supplier_b", "supplier", ["electronics"])
        return engine

    def test_good_supplier_outscores_bad_supplier(self, reputation):
        # Supplier A: 5 successes
        for _ in range(5):
            reputation.record_success("supplier_a", "electronics", quality_score=0.95)
        # Supplier B: 3 successes, 2 failures
        for _ in range(3):
            reputation.record_success("supplier_b", "electronics", quality_score=0.90)
        for _ in range(2):
            reputation.record_failure("supplier_b", "electronics", "quality_fail")

        score_a = reputation.get_score("supplier_a", "electronics")
        score_b = reputation.get_score("supplier_b", "electronics")
        assert score_a > score_b

    def test_reputation_affects_bid_scoring(self, reputation):
        reputation.record_success("supplier_a", "electronics", quality_score=0.95)
        reputation.record_failure("supplier_b", "electronics", "quality_fail")

        rep_a = reputation.get_score("supplier_a", "electronics")
        rep_b = reputation.get_score("supplier_b", "electronics")

        # Same price bid — reputation should differentiate
        score_a = reputation.score_bid(
            price=100, max_price=120, reputation=rep_a,
            estimated_time=10, deadline=60, confidence=0.5,
        )
        score_b = reputation.score_bid(
            price=100, max_price=120, reputation=rep_b,
            estimated_time=10, deadline=60, confidence=0.5,
        )
        assert score_a > score_b

    def test_decay_normalizes_over_time(self, reputation):
        # Build up high reputation
        for _ in range(10):
            reputation.record_success("supplier_a", "electronics", quality_score=0.99)
        high_score = reputation.get_score("supplier_a", "electronics")

        # Apply many decay cycles
        for _ in range(50):
            reputation.apply_decay()
        decayed_score = reputation.get_score("supplier_a", "electronics")

        # Score should have moved toward 0.5
        assert abs(decayed_score - 0.5) < abs(high_score - 0.5)
        assert abs(decayed_score - 0.5) < abs(high_score - 0.5)
        # Score should have moved toward 0.5
        assert abs(decayed_score - 0.5) < abs(high_score - 0.5)
        assert abs(decayed_score - 0.5) < abs(high_score - 0.5)

        # Score should have moved toward 0.5
        assert abs(decayed_score - 0.5) < abs(high_score - 0.5)
        assert abs(decayed_score - 0.5) < abs(high_score - 0.5)
