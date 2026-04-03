"""Tests for the negotiation engine and bidding strategies."""

import pytest
from mesh.core.messages import SupplierBid
from mesh.negotiation.engine import NegotiationEngine, NegotiationState
from mesh.negotiation.strategies import (
    AggressiveStrategy,
    ConservativeStrategy,
    AdaptiveStrategy,
    NegotiationContext,
    StrategyType,
    get_strategy,
)


class TestBiddingStrategies:
    def _ctx(self, role="buyer", current_round=1):
        return NegotiationContext(
            my_role=role,
            original_price=110,
            max_price=120,
            market_price=100,
            num_competing_bids=2,
            current_round=current_round,
            max_rounds=3,
            my_reputation=0.7,
            counterparty_reputation=0.6,
        )

    def test_aggressive_buyer_counters_below_market(self):
        strategy = AggressiveStrategy()
        ctx = self._ctx("buyer")
        price = strategy.compute_counter(ctx, 110)
        assert price < 110

    def test_conservative_buyer_small_discount(self):
        strategy = ConservativeStrategy()
        ctx = self._ctx("buyer")
        price = strategy.compute_counter(ctx, 110)
        assert 100 < price < 110

    def test_adaptive_adjusts_with_competition(self):
        strategy = AdaptiveStrategy()
        ctx_low = NegotiationContext(
            my_role="buyer", original_price=110, max_price=120, market_price=100,
            num_competing_bids=1, current_round=1, max_rounds=3,
            my_reputation=0.5, counterparty_reputation=0.5,
        )
        ctx_high = NegotiationContext(
            my_role="buyer", original_price=110, max_price=120, market_price=100,
            num_competing_bids=5, current_round=1, max_rounds=3,
            my_reputation=0.5, counterparty_reputation=0.5,
        )
        price_low_comp = strategy.compute_counter(ctx_low, 110)
        price_high_comp = strategy.compute_counter(ctx_high, 110)
        assert price_high_comp < price_low_comp  # More competition = more aggressive

    def test_supplier_aggressive_holds_firm(self):
        strategy = AggressiveStrategy()
        ctx = self._ctx("supplier")
        price = strategy.compute_counter(ctx, 100)
        assert price >= 95  # Only 5% discount

    def test_get_strategy_factory(self):
        for st in StrategyType:
            s = get_strategy(st)
            assert s is not None


class TestNegotiationEngine:
    def _make_bids(self, order_id: str):
        return [
            SupplierBid(order_id=order_id, supplier_id="sup_a", price_per_unit=105, available_quantity=50),
            SupplierBid(order_id=order_id, supplier_id="sup_b", price_per_unit=110, available_quantity=50),
        ]

    def test_create_session(self):
        engine = NegotiationEngine()
        session = engine.create_session("o1", "buyer1", 120, 100, 0.85, 10, 15)
        assert session.order_id == "o1"
        assert session.state == NegotiationState.COLLECTING_BIDS

    def test_add_bids(self):
        engine = NegotiationEngine()
        session = engine.create_session("o1", "buyer1", 120, 100, 0.85, 10, 15)
        for bid in self._make_bids("o1"):
            session.add_bid(bid)
        assert len(session.bids) == 2

    def test_evaluate_bids_returns_best(self):
        engine = NegotiationEngine()
        engine.create_session("o1", "buyer1", 120, 100, 0.85, 10, 15)
        for bid in self._make_bids("o1"):
            engine.get_session("o1").add_bid(bid)
        best, should_counter = engine.evaluate_bids("o1")
        assert best is not None
        assert best.supplier_id == "sup_a"  # Cheaper

    def test_evaluate_no_bids_returns_none(self):
        engine = NegotiationEngine()
        engine.create_session("o1", "buyer1", 120, 100, 0.85, 10, 15)
        best, counter = engine.evaluate_bids("o1")
        assert best is None

    def test_generate_counter(self):
        engine = NegotiationEngine()
        session = engine.create_session("o1", "buyer1", 120, 100, 0.85, 10, 15)
        bid = SupplierBid(order_id="o1", supplier_id="sup_a", price_per_unit=115, available_quantity=50)
        session.add_bid(bid)
        session.state = NegotiationState.EVALUATING
        counter = engine.generate_counter("o1", bid)
        assert counter is not None
        assert counter.proposed_price_per_unit < 115

    def test_accept_bid_sets_winner(self):
        engine = NegotiationEngine()
        session = engine.create_session("o1", "buyer1", 120, 100, 0.85, 10, 15)
        bid = SupplierBid(order_id="o1", supplier_id="sup_a", price_per_unit=95, available_quantity=50)
        engine.accept_bid("o1", bid)
        assert session.winner_supplier_id == "sup_a"
        assert session.state == NegotiationState.ACCEPTED

    def test_max_rounds_enforced(self):
        engine = NegotiationEngine()
        session = engine.create_session("o1", "buyer1", 120, 100, 0.85, 10, 15, max_rounds=2)
        bid = SupplierBid(order_id="o1", supplier_id="sup_a", price_per_unit=115, available_quantity=50)
        session.add_bid(bid)
        session.state = NegotiationState.EVALUATING
        # Round 1
        engine.generate_counter("o1", bid)
        # Round 2
        engine.generate_counter("o1", bid)
        # Round 3 should not be allowed
        assert not session.can_counter

    def test_timeout_session(self):
        engine = NegotiationEngine()
        engine.create_session("o1", "buyer1", 120, 100, 0.85, 10, 15)
        engine.timeout_session("o1")
        session = engine.get_session("o1")
        assert session.state == NegotiationState.TIMED_OUT
