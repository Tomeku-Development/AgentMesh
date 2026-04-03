"""Tests for per-capability reputation engine."""

import pytest
from mesh.core.reputation import ReputationEngine, REWARD_SUCCESS, PENALTY_QUALITY_FAIL


class TestReputationEngine:
    def test_initial_score_is_neutral(self, reputation):
        score = reputation.get_score("supplier_001", "electronics")
        assert score == 0.5

    def test_unknown_agent_returns_neutral(self, reputation):
        assert reputation.get_score("unknown_agent", "anything") == 0.5

    def test_success_increases_score(self, reputation):
        update = reputation.record_success(
            "supplier_001", "electronics", on_time=True, quality_score=0.95, order_id="o1"
        )
        assert update is not None
        assert update.new_score > 0.5
        assert update.new_score == pytest.approx(0.5 + REWARD_SUCCESS + 0.03 + 0.02)  # success + on_time + high_quality

    def test_failure_decreases_score(self, reputation):
        reputation.record_success("supplier_001", "electronics")  # Raise above 0.5
        update = reputation.record_failure("supplier_001", "electronics", "quality_fail", "o1")
        assert update is not None
        assert update.new_score < update.old_score

    def test_score_capped_at_max(self, reputation):
        for i in range(30):
            reputation.record_success("supplier_001", "electronics", quality_score=0.99)
        profile = reputation.get_profile("supplier_001")
        cs = profile.get_score("electronics")
        assert cs.score <= 1.0

    def test_score_floored_at_min(self, reputation):
        for i in range(20):
            reputation.record_failure("supplier_001", "electronics", "byzantine")
        profile = reputation.get_profile("supplier_001")
        cs = profile.get_score("electronics")
        assert cs.score >= 0.0

    def test_decay_moves_toward_neutral(self, reputation):
        reputation.record_success("supplier_001", "electronics", quality_score=0.95)
        score_before = reputation.get_score("supplier_001", "electronics")
        reputation.apply_decay()
        score_after = reputation.get_score("supplier_001", "electronics")
        assert abs(score_after - 0.5) < abs(score_before - 0.5)

    def test_confidence_grows_with_transactions(self, reputation):
        profile = reputation.get_profile("supplier_001")
        cs = profile.get_score("electronics")
        assert cs.confidence == 0.0
        reputation.record_success("supplier_001", "electronics")
        assert cs.confidence > 0.0

    def test_per_capability_scores_independent(self, reputation):
        reputation.record_success("supplier_001", "displays", quality_score=0.99)
        reputation.record_failure("supplier_001", "electronics", "quality_fail")
        displays_score = reputation.get_score("supplier_001", "displays")
        electronics_score = reputation.get_score("supplier_001", "electronics")
        assert displays_score > electronics_score

    def test_overall_score_is_weighted_average(self, reputation):
        reputation.record_success("supplier_001", "electronics", quality_score=0.99)
        profile = reputation.get_profile("supplier_001")
        overall = profile.overall_score
        assert 0.0 <= overall <= 1.0

    def test_bid_scoring(self, reputation):
        score = reputation.score_bid(
            price=100, max_price=120, reputation=0.8,
            estimated_time=5, deadline=30, confidence=0.6,
        )
        assert 0.0 <= score <= 1.0

    def test_bid_scoring_lower_price_scores_higher(self, reputation):
        score_low = reputation.score_bid(price=80, max_price=120, reputation=0.5, estimated_time=10, deadline=30, confidence=0.5)
        score_high = reputation.score_bid(price=110, max_price=120, reputation=0.5, estimated_time=10, deadline=30, confidence=0.5)
        assert score_low > score_high
