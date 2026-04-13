"""LogisticsAgent — bids on shipping tasks, routes deliveries."""

from __future__ import annotations

import asyncio
import logging
import random
import threading
import time

from mesh.agents.base import BaseAgent
from mesh.core import topics
from mesh.core.messages import (
    MessageEnvelope,
    ShippingAssign,
    ShippingBid,
    TransitUpdate,
)
from mesh.llm.prompts import logistics_pricing_prompt
from mesh.llm.router import LLMDisabledError, LLMProviderError, LLMRouter

logger = logging.getLogger(__name__)


class LogisticsAgent(BaseAgent):
    """Bids on shipping tasks, simulates transit, confirms deliveries."""

    def __init__(self, config, identity=None, ledger=None, reputation=None):
        config.agent_role = "logistics"
        super().__init__(config, identity, ledger, reputation)
        self._active_shipments: dict[str, dict] = {}
        self._vehicle_type = "truck"
        self._llm_router = LLMRouter(config)

    def _subscribe_topics(self) -> None:
        self.transport.subscribe("mesh/shipping/+/request", qos=1)
        self.transport.subscribe("mesh/shipping/+/assign", qos=1)

    def _handle_message(self, topic: str, envelope: MessageEnvelope) -> None:
        payload = envelope.payload

        if "/request" in topic and "quality" not in topic and "orders" not in topic:
            self._handle_shipping_request(payload)
        elif "/assign" in topic:
            self._handle_assignment(payload)

    def _handle_shipping_request(self, payload: dict) -> None:
        """Bid on a shipping request."""
        shipment_id = payload.get("shipment_id", "")
        order_id = payload.get("order_id", "")
        weight = payload.get("weight_kg", 10)
        fragile = payload.get("fragile", False)
        deadline = payload.get("deadline_seconds", 30)
        origin = payload.get("origin", "unknown")
        destination = payload.get("destination", "unknown")

        # Try LLM first for pricing decision
        price = None
        transit_time = None
        llm_used = False

        try:
            system_prompt, user_prompt = logistics_pricing_prompt(
                weight=weight,
                fragile=fragile,
                origin=origin,
                destination=destination,
                deadline=deadline,
                current_load=self._active_orders,
                vehicle_type=self._vehicle_type,
            )
            result = asyncio.run(self._llm_router.complete_json(user_prompt, system_prompt))

            llm_price = result.get("price")
            llm_transit = result.get("estimated_epochs", result.get("estimated_transit_seconds"))

            # Validate LLM output
            min_price = weight * 1.0  # minimum rate
            max_price = weight * 10.0  # sanity cap

            if llm_price is not None and min_price <= llm_price <= max_price:
                price = round(llm_price, 2)
                llm_used = True
                logger.info(
                    "[%s] LLM pricing for shipment %s: $%.2f (reasoning: %s)",
                    self.agent_id, shipment_id[:8], price, result.get("reasoning", "N/A")[:50]
                )
            else:
                logger.warning(
                    "[%s] LLM price %.2f invalid "
                    "(weight=%.1f, bounds=[%.2f, %.2f]), "
                    "using fallback",
                    self.agent_id, llm_price, weight, min_price, max_price
                )

            if llm_transit is not None and 0 < llm_transit <= deadline:
                transit_time = int(llm_transit)
            elif llm_transit is not None:
                logger.warning(
                    "[%s] LLM transit %d invalid (deadline=%d), using fallback",
                    self.agent_id, llm_transit, deadline
                )

        except (LLMDisabledError, LLMProviderError, Exception) as e:
            logger.warning(
                "[%s] LLM failed for shipping pricing: %s, "
                "using fallback",
                self.agent_id, str(e)[:100],
            )

        # Fallback to original calculation if LLM didn't provide valid price
        if price is None:
            base_rate = 2.0  # per kg
            fragile_surcharge = 1.5 if fragile else 1.0
            price = round(weight * base_rate * fragile_surcharge * random.uniform(0.9, 1.1), 2)

        if transit_time is None:
            transit_time = random.randint(5, 15)

        bid = ShippingBid(
            shipment_id=shipment_id,
            logistics_id=self.agent_id,
            price=price,
            estimated_transit_seconds=transit_time,
            vehicle_type=self._vehicle_type,
        )
        self.publish(topics.shipping_bid(shipment_id), bid)
        logger.info(
            "[%s] Shipping bid for %s: $%.2f, %ds (LLM: %s)",
            self.agent_id, shipment_id[:8], price, transit_time, llm_used
        )

        # Auto-assign (since we're the only logistics agent in demo)
        # In production, supplier would pick best bid
        timer = threading.Timer(2.0, self._auto_assign, args=[shipment_id, order_id, price])
        timer.daemon = True
        timer.start()

    def _auto_assign(self, shipment_id: str, order_id: str, price: float) -> None:
        """Self-assign shipping (simplified for demo — supplier would normally assign)."""
        assign = ShippingAssign(
            shipment_id=shipment_id,
            order_id=order_id,
            logistics_id=self.agent_id,
            accepted_bid_id="auto",
            price=price,
        )
        self.publish(topics.shipping_assign(shipment_id), assign)

    def _handle_assignment(self, payload: dict) -> None:
        """Start shipping a package."""
        if payload.get("logistics_id") != self.agent_id:
            return

        shipment_id = payload.get("shipment_id", "")
        order_id = payload.get("order_id", "")

        self._active_shipments[shipment_id] = {
            "order_id": order_id,
            "status": "assigned",
            "started": time.time(),
        }
        self._active_orders += 1

        logger.info(
            "[%s] Assigned shipment %s for order %s",
            self.agent_id, shipment_id[:8], order_id[:8],
        )

        # Simulate transit phases
        thread = threading.Thread(
            target=self._simulate_transit,
            args=[shipment_id, order_id],
            daemon=True,
        )
        thread.start()

    def _simulate_transit(self, shipment_id: str, order_id: str) -> None:
        """Simulate the shipping lifecycle with transit updates."""
        phases = [
            ("picked_up", 2),
            ("in_transit", 4),
            ("out_for_delivery", 2),
            ("delivered", 0),
        ]

        for status, delay in phases:
            if not self._running:
                return

            eta = sum(d for _, d in phases[phases.index((status, delay)) + 1:])
            update = TransitUpdate(
                shipment_id=shipment_id,
                logistics_id=self.agent_id,
                status=status,
                eta_seconds=eta,
                condition="good",
            )
            self.publish(topics.shipping_transit(shipment_id), update)
            logger.info("[%s] Shipment %s: %s", self.agent_id, shipment_id[:8], status)

            if status == "delivered":
                # Publish delivery confirmation with order_id for buyer
                deliver_payload = {
                    "shipment_id": shipment_id,
                    "order_id": order_id,
                    "logistics_id": self.agent_id,
                    "condition": "good",
                }
                from mesh.core.protocol import build_envelope
                env = build_envelope(self.agent_id, self.role, deliver_payload, self.hlc)
                self.transport.publish(topics.shipping_deliver(shipment_id), env)

                # Confirm back to supplier
                confirm_payload = {
                    "shipment_id": shipment_id,
                    "order_id": order_id,
                    "logistics_id": self.agent_id,
                    "delivered_at": time.time(),
                }
                env2 = build_envelope(self.agent_id, self.role, confirm_payload, self.hlc)
                self.transport.publish(topics.shipping_confirm(shipment_id), env2)

                self._active_orders = max(0, self._active_orders - 1)
                break

            time.sleep(delay)
