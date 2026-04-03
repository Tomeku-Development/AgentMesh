"""QualityInspectorAgent — verifies deliveries, scores quality."""

from __future__ import annotations

import logging
import random
import time
import threading

from mesh.agents.base import BaseAgent
from mesh.core.messages import InspectionReport, MessageEnvelope
from mesh.core import topics

logger = logging.getLogger(__name__)


class InspectorAgent(BaseAgent):
    """Inspects delivered goods, scores quality, flags defects."""

    def __init__(self, config, identity=None, ledger=None, reputation=None):
        config.agent_role = "inspector"
        super().__init__(config, identity, ledger, reputation)

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

        logger.info(
            "[%s] Inspecting delivery for order %s (%dx %s)",
            self.agent_id, order_id[:8], quantity_expected, goods,
        )

        # Simulate inspection delay
        time.sleep(random.uniform(1, 3))

        # Simulate quality results
        # Most orders pass (80% chance of good quality)
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
            defect_descriptions = [
                f"{defective} units with cosmetic damage",
            ]

        recommendation = "accept"
        if not passed:
            recommendation = "reject"
        elif defective > 0:
            recommendation = "partial_accept"

        report = InspectionReport(
            inspection_id=inspection_id,
            order_id=order_id,
            shipment_id=shipment_id,
            inspector_id=self.agent_id,
            quality_score=round(quality_score, 3),
            quantity_verified=quantity_verified,
            quantity_defective=defective,
            defect_descriptions=defect_descriptions,
            passed=passed,
            recommendation=recommendation,
        )
        self.publish(topics.quality_report(inspection_id), report)

        logger.info(
            "[%s] Inspection %s: score=%.3f, verified=%d, defective=%d, passed=%s",
            self.agent_id, inspection_id[:8], quality_score,
            quantity_verified, defective, passed,
        )
