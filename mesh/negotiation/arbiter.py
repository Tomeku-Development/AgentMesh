"""Dispute resolution and penalty assessment."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Literal

from mesh.core.ledger import Ledger
from mesh.core.reputation import ReputationEngine
from mesh.llm.prompts import arbiter_dispute_prompt
from mesh.llm.router import LLMDisabledError, LLMProviderError, LLMRouter


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

    def __init__(
        self,
        ledger: Ledger,
        reputation: ReputationEngine,
        llm_router: LLMRouter | None = None,
    ) -> None:
        self._ledger = ledger
        self._reputation = reputation
        self._llm_router = llm_router
        self._logger = logging.getLogger(__name__)

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
        defect_ratio = quantity_defective / max(1, quantity_expected)

        # Try LLM-based resolution if router is available
        if self._llm_router is not None:
            try:
                system_prompt, user_prompt = arbiter_dispute_prompt(
                    quality_score,
                    quality_threshold,
                    defect_ratio,
                    {},
                )
                result = asyncio.run(self._llm_router.complete_json(user_prompt, system_prompt))

                # Parse result - expect {outcome, refund_percentage, supplier_penalty, reasoning}
                outcome = result.get("outcome", "accepted")
                refund_percentage = float(result.get("refund_percentage", 0.0))
                supplier_penalty = float(result.get("supplier_penalty", 0.0))

                # Validate outcome
                valid_outcomes = ["accepted", "partial_refund", "full_refund"]
                if outcome not in valid_outcomes:
                    outcome = "accepted"

                # Validate bounds: refund in [0, 1], penalty in [-0.20, 0]
                refund_percentage = max(0.0, min(1.0, refund_percentage))
                supplier_penalty = max(-0.15, min(0.0, supplier_penalty))

                # Record failure for non-accepted outcomes
                if outcome != "accepted":
                    self._reputation.record_failure(
                        supplier_id, capability, reason="quality_fail", order_id=order_id
                    )

                self._logger.info(
                    "LLM dispute resolution: %s (refund: %.2f, penalty: %.2f) - %s",
                    outcome,
                    refund_percentage,
                    supplier_penalty,
                    result.get("reasoning", ""),
                )

                return DisputeResolution(
                    order_id=order_id,
                    outcome=outcome,
                    refund_percentage=refund_percentage,
                    supplier_penalty=supplier_penalty,
                    reason=result.get("reasoning", f"LLM resolution: {outcome}"),
                )
            except (LLMDisabledError, LLMProviderError, ValueError, KeyError) as e:
                self._logger.warning(
                    "LLM dispute resolution failed, "
                    "using deterministic fallback: %s", e,
                )
            except Exception as e:
                self._logger.warning("LLM dispute resolution error: %s", e)

        # Fallback: Deterministic resolution
        if quality_score >= quality_threshold:
            return DisputeResolution(
                order_id=order_id,
                outcome="accepted",
                refund_percentage=0.0,
                supplier_penalty=0.0,
                reason="Quality meets threshold",
            )

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
                reason=(
                    f"Quality {quality_score:.2f} below threshold "
                    f"{quality_threshold:.2f}, "
                    f"{quantity_defective} defective"
                ),
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

        # Try LLM-based penalty assessment if router is available
        if self._llm_router is not None:
            try:
                system_prompt = (
                    "You are an Arbiter agent assessing "
                    "late delivery penalties in the MESH "
                    "supply chain.\n"
                    "Your role is to determine a fair penalty "
                    "percentage based on lateness severity.\n"
                    "\n"
                    "You must respond with a JSON object containing:\n"
                    "{\n"
                    '    "penalty_percentage": float,\n'
                    '    "reasoning": "brief explanation",\n'
                    '    "severity": "minor" | "moderate" | "severe"\n'
                    "}\n"
                    "\n"
                    "Constraints:\n"
                    "- penalty_percentage must be between 0.0 and 0.15\n"
                    "- Minor lateness (<10%) should be around 0.02-0.03\n"
                    "- Moderate lateness (10-25%): around 0.05-0.08\n"
                    "- Severe lateness (>25%): around 0.10-0.15"
                )

                user_prompt = f"""Assess late delivery penalty.

## Delivery Details
- Seconds late: {seconds_late:.1f}
- Expected deadline: {deadline_seconds:.1f} seconds
- Lateness ratio: {lateness_ratio:.2%}

## Guidelines
- Lateness ratio < 10%: Minor penalty (~2-3%)
- Lateness ratio 10-25%: Moderate penalty (~5-8%)
- Lateness ratio > 25%: Severe penalty (~10-15%)

Respond with your penalty assessment as JSON."""

                result = asyncio.run(self._llm_router.complete_json(user_prompt, system_prompt))
                penalty = float(result.get("penalty_percentage", 0.02))

                # Validate penalty bounds [0, 0.15]
                penalty = max(0.0, min(0.15, penalty))

                # Always record failure for late delivery
                self._reputation.record_failure(
                    logistics_id, "shipping", reason="late_delivery", order_id=order_id
                )
                if lateness_ratio >= 0.25:
                    self._reputation.record_failure(
                        supplier_id, capability, reason="late_delivery", order_id=order_id
                    )

                self._logger.info(
                    "LLM late delivery penalty: %.2f for order %s (%s)",
                    penalty,
                    order_id,
                    result.get("reasoning", ""),
                )
                return penalty
            except (LLMDisabledError, LLMProviderError, ValueError, KeyError) as e:
                self._logger.warning(
                    "LLM late delivery assessment failed, "
                    "using deterministic fallback: %s", e,
                )
            except Exception as e:
                self._logger.warning("LLM late delivery assessment error: %s", e)

        # Fallback: Deterministic tier-based penalty
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
