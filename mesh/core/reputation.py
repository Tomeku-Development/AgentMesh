"""Per-capability reputation scoring engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mesh.core.messages import ReputationUpdate


@dataclass
class CapabilityScore:
    """Reputation score for a specific capability."""
    capability: str
    score: float = 0.5      # 0.0 - 1.0, starts neutral
    confidence: float = 0.0  # 0.0 - 1.0, increases with observations
    transaction_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    epochs_since_update: int = 0


@dataclass
class ReputationProfile:
    """An agent's full reputation across all capabilities."""
    agent_id: str
    role: str
    capabilities: dict[str, CapabilityScore] = field(default_factory=dict)
    total_transactions: int = 0

    def get_score(self, capability: str) -> CapabilityScore:
        """Get or create a capability score."""
        if capability not in self.capabilities:
            self.capabilities[capability] = CapabilityScore(capability=capability)
        return self.capabilities[capability]

    @property
    def overall_score(self) -> float:
        """Weighted average of all capability scores."""
        if not self.capabilities:
            return 0.5
        total_weight = 0.0
        weighted_sum = 0.0
        for cs in self.capabilities.values():
            weight = max(0.1, cs.confidence)
            weighted_sum += cs.score * weight
            total_weight += weight
        return weighted_sum / total_weight if total_weight > 0 else 0.5


# ── Scoring Constants ──────────────────────────────────

REWARD_SUCCESS = 0.05
REWARD_ON_TIME = 0.03
REWARD_HIGH_QUALITY = 0.02
PENALTY_LATE = -0.04
PENALTY_QUALITY_FAIL = -0.08
PENALTY_NO_SHOW = -0.15
PENALTY_BYZANTINE = -0.25
DECAY_FACTOR = 0.98
CONFIDENCE_GROWTH = 0.05
MIN_SCORE = 0.0
MAX_SCORE = 1.0


class ReputationEngine:
    """Manages reputation profiles for all agents in the mesh.

    Deterministic: given the same BFT-ordered event stream, all agents
    will compute identical reputation states.
    """

    def __init__(self, decay_factor: float = DECAY_FACTOR) -> None:
        self._profiles: dict[str, ReputationProfile] = {}
        self._decay_factor = decay_factor
        self._updates: list[ReputationUpdate] = []

    def register(self, agent_id: str, role: str, capabilities: list[str] | None = None) -> None:
        """Register an agent with initial reputation."""
        if agent_id not in self._profiles:
            profile = ReputationProfile(agent_id=agent_id, role=role)
            for cap in (capabilities or []):
                profile.capabilities[cap] = CapabilityScore(capability=cap)
            self._profiles[agent_id] = profile

    def get_profile(self, agent_id: str) -> ReputationProfile | None:
        return self._profiles.get(agent_id)

    def get_score(self, agent_id: str, capability: str) -> float:
        """Get an agent's score for a specific capability."""
        profile = self._profiles.get(agent_id)
        if not profile:
            return 0.5
        cs = profile.capabilities.get(capability)
        return cs.score if cs else 0.5

    def record_success(
        self,
        agent_id: str,
        capability: str,
        on_time: bool = True,
        quality_score: float = 0.9,
        order_id: str = "",
    ) -> ReputationUpdate | None:
        """Record a successful interaction."""
        profile = self._profiles.get(agent_id)
        if not profile:
            return None

        cs = profile.get_score(capability)
        old_score = cs.score

        delta = REWARD_SUCCESS
        if on_time:
            delta += REWARD_ON_TIME
        if quality_score > 0.9:
            delta += REWARD_HIGH_QUALITY

        cs.score = min(MAX_SCORE, cs.score + delta)
        cs.transaction_count += 1
        cs.success_count += 1
        cs.confidence = min(1.0, cs.confidence + CONFIDENCE_GROWTH)
        cs.epochs_since_update = 0
        profile.total_transactions += 1

        update = ReputationUpdate(
            subject_id=agent_id,
            capability=capability,
            old_score=old_score,
            new_score=cs.score,
            reason="order_fulfilled",
            evidence_order_id=order_id,
        )
        self._updates.append(update)
        return update

    def record_failure(
        self,
        agent_id: str,
        capability: str,
        reason: str = "quality_fail",
        order_id: str = "",
    ) -> ReputationUpdate | None:
        """Record a failed interaction."""
        profile = self._profiles.get(agent_id)
        if not profile:
            return None

        cs = profile.get_score(capability)
        old_score = cs.score

        penalty_map = {
            "late_delivery": PENALTY_LATE,
            "quality_fail": PENALTY_QUALITY_FAIL,
            "no_show": PENALTY_NO_SHOW,
            "byzantine": PENALTY_BYZANTINE,
        }
        delta = penalty_map.get(reason, PENALTY_QUALITY_FAIL)

        cs.score = max(MIN_SCORE, cs.score + delta)
        cs.transaction_count += 1
        cs.failure_count += 1
        cs.confidence = min(1.0, cs.confidence + CONFIDENCE_GROWTH)
        cs.epochs_since_update = 0
        profile.total_transactions += 1

        update = ReputationUpdate(
            subject_id=agent_id,
            capability=capability,
            old_score=old_score,
            new_score=cs.score,
            reason=reason,
            evidence_order_id=order_id,
        )
        self._updates.append(update)
        return update

    def apply_decay(self) -> list[ReputationUpdate]:
        """Apply epoch-based decay to all scores. Returns updates for changed scores."""
        updates = []
        for profile in self._profiles.values():
            for cs in profile.capabilities.values():
                cs.epochs_since_update += 1
                old_score = cs.score
                # Decay toward neutral (0.5)
                cs.score = 0.5 + (cs.score - 0.5) * self._decay_factor
                if abs(cs.score - old_score) > 0.001:
                    update = ReputationUpdate(
                        subject_id=profile.agent_id,
                        capability=cs.capability,
                        old_score=old_score,
                        new_score=cs.score,
                        reason="decay",
                    )
                    updates.append(update)
                    self._updates.append(update)
        return updates

    def score_bid(
        self,
        price: float,
        max_price: float,
        reputation: float,
        estimated_time: float,
        deadline: float,
        confidence: float,
        w_price: float = 0.35,
        w_rep: float = 0.30,
        w_speed: float = 0.20,
        w_conf: float = 0.15,
    ) -> float:
        """Score a bid using weighted criteria. Higher is better."""
        price_score = max(0.0, 1.0 - (price / max_price)) if max_price > 0 else 0.0
        speed_score = max(0.0, 1.0 - (estimated_time / deadline)) if deadline > 0 else 0.0
        return (
            w_price * price_score
            + w_rep * reputation
            + w_speed * speed_score
            + w_conf * confidence
        )

    def all_profiles(self) -> list[ReputationProfile]:
        return list(self._profiles.values())

    @property
    def recent_updates(self) -> list[ReputationUpdate]:
        return self._updates[-50:]
