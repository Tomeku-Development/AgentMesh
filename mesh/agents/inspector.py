"""QualityInspectorAgent — verifies deliveries, scores quality."""

from __future__ import annotations

import asyncio
import logging
import random
import time

from mesh.agents.base import BaseAgent
from mesh.core import topics
from mesh.core.messages import InspectionReport, MessageEnvelope
from mesh.llm.prompts import inspector_quality_prompt
from mesh.llm.router import LLMRouter

logger = logging.getLogger(__name__)


class InspectorAgent(BaseAgent):
    """Inspects delivered goods, scores quality, flags defects."""

    def __init__(self, config, identity=None, ledger=None, reputation=None):
        config.agent_role = "inspector"
        super().__init__(config, identity, ledger, reputation)
        self._llm_router = LLMRouter(config)

    def _subscribe_topics(self) -> None:
        self.transport.subscribe("mesh/quality/+/request", qos=1)

    def _handle_message(self, topic: str, envelope: MessageEnvelope) -> None:
        payload = envelope.payload
        if "/request" in topic and "quality" in topic:
            self._handle_inspection_request(payload)

    def _handle_inspection_request(self, payload: dict) -> None:
        """Perform quality inspection on a delivery."""
        inspection_id = payload.get("inspection_id", "")
        order_id = payload.get("order_id", "")
        shipment_id = payload.get("shipment_id", "")
        goods = payload.get("goods", "")
        quantity_expected = payload.get("quantity_expected", 0)
        quality_threshold = payload.get("quality_threshold", 0.85)
        supplier_id = payload.get("supplier_id", "")

        logger.info(
            "[%s] Inspecting delivery for order %s (%dx %s)",
            self.agent_id, order_id[:8], quantity_expected, goods,
        )

        # Simulate inspection delay (physical inspection time)
        time.sleep(random.uniform(1, 3))

        # Try LLM-based inspection, fall back to random on failure
        try:
            result = self._llm_inspection(
                goods, quantity_expected, quality_threshold, supplier_id
            )
            logger.info(
                "[%s] Inspection %s (LLM): score=%.3f, verified=%d, defective=%d, passed=%s",
                self.agent_id, inspection_id[:8], result["quality_score"],
                result["quantity_verified"], result["quantity_defective"], result["passed"],
            )
        except Exception as e:
            logger.warning(
                "[%s] LLM inspection failed, using fallback: %s", self.agent_id, e
            )
            result = self._fallback_inspection(quantity_expected, quality_threshold)
            logger.info(
                "[%s] Inspection %s (fallback): score=%.3f, verified=%d, defective=%d, passed=%s",
                self.agent_id, inspection_id[:8], result["quality_score"],
                result["quantity_verified"], result["quantity_defective"], result["passed"],
            )

        report = InspectionReport(
            inspection_id=inspection_id,
            order_id=order_id,
            shipment_id=shipment_id,
            inspector_id=self.agent_id,
            quality_score=round(result["quality_score"], 3),
            quantity_verified=result["quantity_verified"],
            quantity_defective=result["quantity_defective"],
            defect_descriptions=result["defect_descriptions"],
            passed=result["passed"],
            recommendation=result["recommendation"],
        )
        self.publish(topics.quality_report(inspection_id), report)

    def _llm_inspection(
        self,
        goods: str,
        quantity_expected: int,
        quality_threshold: float,
        supplier_id: str,
    ) -> dict:
        """Use LLM to assess quality. Raises on failure."""
        # Get supplier reputation if available
        supplier_reputation = 0.5  # default
        if self.reputation and supplier_id:
            try:
                supplier_reputation = self.reputation.get_score(supplier_id)
            except Exception:
                pass  # Use default

        # Determine category from goods name (simple heuristic)
        category = "general"
        goods_lower = goods.lower()
        if any(x in goods_lower for x in ["phone", "laptop", "tablet", "chip", "board"]):
            category = "electronics"
        elif any(x in goods_lower for x in ["shirt", "fabric", "textile", "cotton"]):
            category = "textiles"
        elif any(x in goods_lower for x in ["food", "grain", "produce", "fruit"]):
            category = "food"

        system_prompt, user_prompt = inspector_quality_prompt(
            goods, quantity_expected, supplier_reputation, category
        )

        result = asyncio.run(self._llm_router.complete_json(user_prompt, system_prompt))

        # Parse and validate LLM response
        quality_score = float(result.get("quality_score", 0.7))
        defect_count = int(result.get("defect_count", 0))
        recommendation = result.get("recommendation", "accept")

        # Validate: quality_score in [0, 1]
        quality_score = max(0.0, min(1.0, quality_score))

        # Validate: defect_count >= 0 and <= quantity_expected
        defect_count = max(0, min(quantity_expected, defect_count))

        # Validate: recommendation in valid set
        valid_recs = ["accept", "conditional", "reject"]
        if recommendation not in valid_recs:
            recommendation = "accept" if quality_score >= quality_threshold else "reject"

        # Map "conditional" to "partial_accept" for consistency with original logic
        if recommendation == "conditional":
            recommendation = "partial_accept"

        # Validate: recommendation should align with quality_threshold
        # But allow LLM discretion for edge cases
        final_recommendation = recommendation
        if recommendation not in valid_recs + ["partial_accept"]:
            final_recommendation = "accept" if quality_score >= quality_threshold else "reject"

        # Derive passed from quality_score vs threshold
        passed = quality_score >= quality_threshold

        quantity_verified = quantity_expected - defect_count
        defect_descriptions = result.get("findings", [])
        if defect_count > 0 and not defect_descriptions:
            defect_descriptions = [f"{defect_count} units with quality issues"]

        return {
            "quality_score": quality_score,
            "quantity_verified": quantity_verified,
            "quantity_defective": defect_count,
            "defect_descriptions": defect_descriptions,
            "passed": passed,
            "recommendation": final_recommendation,
        }

    def _fallback_inspection(
        self,
        quantity_expected: int,
        quality_threshold: float,
    ) -> dict:
        """Fallback to random-based inspection when LLM fails."""
        # Original 80% pass rate logic
        if random.random() < 0.80:
            quality_score = random.uniform(0.85, 0.99)
            defective = random.randint(0, max(1, quantity_expected // 20))
        else:
            quality_score = random.uniform(0.50, 0.84)
            defective = random.randint(quantity_expected // 10, quantity_expected // 5)

        quantity_verified = quantity_expected - defective
        passed = quality_score >= quality_threshold

        defect_descriptions = []
        if defective > 0:
            defect_descriptions = [f"{defective} units with cosmetic damage"]

        recommendation = "accept"
        if not passed:
            recommendation = "reject"
        elif defective > 0:
            recommendation = "partial_accept"

        return {
            "quality_score": quality_score,
            "quantity_verified": quantity_verified,
            "quantity_defective": defective,
            "defect_descriptions": defect_descriptions,
            "passed": passed,
            "recommendation": recommendation,
        }
