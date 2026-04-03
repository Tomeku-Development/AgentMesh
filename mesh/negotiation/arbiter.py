"""Dispute resolution and penalty assessment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from mesh.core.ledger import Ledger
from mesh.core.reputation import ReputationEngine


@dataclass
class DisputeResolution:
    """Result of a dispute resolution."""
    order_id: str
    outcome: Literal["accepted", "partial_refund", "full_refund"]
    refund_percentage: float  # 0.0 - 1.0
    supplier_penalty: float  # reputation penalty delta
    reason: str


class Arbiter:
    """Resolves disputes between buyer and supplier based on inspection results.

    Deterministic: same inputs produce same outputs across all agents.
    """

    def __init__(self, ledger: Ledger, reputation: ReputationEngine) -> None:
        self._ledger = ledger
        self._reputation = reputation

    def resolve_quality_dispute(
        self,
        order_id: str,
        supplier_id: str,
        capability: str,
        quality_score: float,
        quality_threshold: float,
        quantity_expected: int,
        quantity_defective: int,
    ) -> DisputeResolution:
        """Resolve a quality inspection dispute.

        Rules:
        - quality_score >= threshold: accepted, no penalties
        - quality_score >= threshold * 0.8: partial refund (proportional to defects)
        - quality_score < threshold * 0.8: full refund, heavy reputation slash
        """
        if quality_score >= quality_threshold:
            return DisputeResolution(
                order_id=order_id,
                outcome="accepted",
                refund_percentage=0.0,
                supplier_penalty=0.0,
                reason="Quality meets threshold",
            )

        defect_ratio = quantity_defective / max(1, quantity_expected)

        if quality_score >= quality_threshold * 0.8:
            # Partial refund — only refund for defective items
            refund_pct = defect_ratio
            self._reputation.record_failure(
                supplier_id, capability, reason="quality_fail", order_id=order_id
            )
            return DisputeResolution(
                order_id=order_id,
                outcome="partial_refund",
                refund_percentage=min(1.0, refund_pct),
                supplier_penalty=-0.08,
                reason=f"Quality {quality_score:.2f} below threshold {quality_threshold:.2f}, {quantity_defective} defective",
            )

        # Full refund — severe quality failure
        self._reputation.record_failure(
            supplier_id, capability, reason="quality_fail", order_id=order_id
        )
        return DisputeResolution(
            order_id=order_id,
            outcome="full_refund",
            refund_percentage=1.0,
            supplier_penalty=-0.15,
            reason=f"Severe quality failure: {quality_score:.2f} << {quality_threshold:.2f}",
        )

    def resolve_late_delivery(
        self,
        order_id: str,
        supplier_id: str,
        logistics_id: str,
        capability: str,
        seconds_late: float,
        deadline_seconds: float,
    ) -> float:
        """Assess late delivery penalty. Returns penalty percentage of order value.

        Tiers:
        - <10% late: warning only, 2% penalty
        - 10-25% late: 5% penalty
        - >25% late: 10% penalty
        """
        lateness_ratio = seconds_late / max(1, deadline_seconds)

        if lateness_ratio < 0.10:
            self._reputation.record_failure(
                logistics_id, "shipping", reason="late_delivery", order_id=order_id
            )
            return 0.02
        elif lateness_ratio < 0.25:
            self._reputation.record_failure(
                logistics_id, "shipping", reason="late_delivery", order_id=order_id
            )
            return 0.05
        else:
            self._reputation.record_failure(
                logistics_id, "shipping", reason="late_delivery", order_id=order_id
            )
            self._reputation.record_failure(
                supplier_id, capability, reason="late_delivery", order_id=order_id
            )
            return 0.10

    def resolve_no_show(
        self,
        order_id: str,
        agent_id: str,
        capability: str,
    ) -> None:
        """Penalize an agent that committed to an order but never showed up."""
        self._reputation.record_failure(
            agent_id, capability, reason="no_show", order_id=order_id
        )
