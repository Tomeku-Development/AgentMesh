"""SupplierAgent — manages inventory, bids on orders, fulfills commitments."""

from __future__ import annotations

import logging
import random
import time
import threading

from mesh.agents.base import BaseAgent
from mesh.core.messages import (
    MessageEnvelope,
    OrderCommit,
    OrderStatus,
    ShippingRequest,
    SupplierBid,
)
from mesh.core import topics
from mesh.negotiation.strategies import (
    AdaptiveStrategy,
    NegotiationContext,
    StrategyType,
    get_strategy,
)

logger = logging.getLogger(__name__)


class SupplierAgent(BaseAgent):
    """Manages inventory, bids on purchase orders, fulfills commitments."""

    def __init__(self, config, identity=None, ledger=None, reputation=None):
        config.agent_role = "supplier"
        super().__init__(config, identity, ledger, reputation)
        self._inventory: dict[str, int] = {}  # goods -> quantity
        self._base_costs: dict[str, float] = {}  # goods -> cost per unit
        self._committed_orders: dict[str, dict] = {}
        self._strategy = get_strategy(StrategyType.ADAPTIVE)
        self._market_prices: dict[str, float] = {}

    def set_inventory(self, inventory: dict[str, int], costs: dict[str, float]) -> None:
        """Set initial inventory and cost basis."""
        self._inventory = dict(inventory)
        self._base_costs = dict(costs)

    def _subscribe_topics(self) -> None:
        self.transport.subscribe("mesh/orders/+/request", qos=1)
        self.transport.subscribe("mesh/orders/+/accept", qos=1)
        self.transport.subscribe("mesh/orders/+/reject", qos=1)
        self.transport.subscribe("mesh/orders/+/counter", qos=1)
        self.transport.subscribe("mesh/shipping/+/confirm", qos=1)
        self.transport.subscribe(topics.MARKET_PRICES, qos=1)

    def _handle_message(self, topic: str, envelope: MessageEnvelope) -> None:
        payload = envelope.payload

        if topic == topics.MARKET_PRICES:
            self._handle_market_prices(payload)
        elif "/request" in topic and "shipping" not in topic and "quality" not in topic:
            self._handle_order_request(payload)
        elif "/accept" in topic:
            self._handle_bid_accepted(payload)
        elif "/reject" in topic:
            self._handle_bid_rejected(payload)
        elif "/counter" in topic:
            self._handle_counter_offer(payload)
        elif "/confirm" in topic and "shipping" in topic:
            self._handle_shipping_confirmed(topic, payload)

    def _handle_market_prices(self, payload: dict) -> None:
        for goods, data in payload.get("prices", {}).items():
            self._market_prices[goods] = data.get("price", 0)

    def _handle_order_request(self, payload: dict) -> None:
        """Evaluate and potentially bid on a purchase order."""
        order_id = payload.get("order_id", "")
        goods = payload.get("goods", "")
        category = payload.get("category", "")
        quantity = payload.get("quantity", 0)
        max_price = payload.get("max_price_per_unit", 0)
        required_caps = payload.get("required_capabilities", [])

        # Check if we can fulfill
        if category not in self.capabilities and not any(c in self.capabilities for c in required_caps):
            return

        available = self._inventory.get(goods, 0)
        if available <= 0:
            return

        # Calculate bid price
        cost = self._base_costs.get(goods, max_price * 0.7)
        market = self._market_prices.get(goods, max_price * 0.9)
        margin = random.uniform(0.05, 0.15)
        bid_price = cost * (1 + margin)

        # Don't bid above max price
        if bid_price > max_price:
            bid_price = max_price * random.uniform(0.90, 0.98)

        # Get our reputation for this category
        rep_score = self.reputation.get_score(self.agent_id, category)

        bid = SupplierBid(
            order_id=order_id,
            supplier_id=self.agent_id,
            price_per_unit=round(bid_price, 2),
            available_quantity=min(available, quantity),
            estimated_fulfillment_seconds=random.randint(5, 15),
            reputation_score=rep_score,
            notes=f"From {self.agent_id[:8]}, {available} in stock",
        )

        self.publish(topics.order_bid(order_id), bid)
        logger.info(
            "[%s] Bid on order %s: %.2f/unit x%d",
            self.agent_id, order_id[:8], bid_price, min(available, quantity),
        )

    def _handle_counter_offer(self, payload: dict) -> None:
        """Respond to buyer's counter-offer."""
        to_agent = payload.get("to_agent", "")
        if to_agent != self.agent_id:
            return

        order_id = payload.get("order_id", "")
        proposed_price = payload.get("proposed_price_per_unit", 0)
        goods_category = ""
        for oid, data in self._committed_orders.items():
            if oid == order_id:
                goods_category = data.get("category", "")

        cost = self._base_costs.get(goods_category, proposed_price * 0.7)

        # Accept if profitable, counter if close, reject if losing money
        if proposed_price >= cost * 1.05:
            # Accept — still profitable
            from mesh.core.messages import CounterOffer
            response = CounterOffer(
                order_id=order_id,
                original_bid_id=payload.get("original_bid_id", ""),
                from_agent=self.agent_id,
                to_agent=payload.get("from_agent", ""),
                round=payload.get("round", 1),
                proposed_price_per_unit=proposed_price,
                justification="Accepted counter-offer",
            )
            self.publish(topics.order_counter(order_id), response)
            logger.info("[%s] Accepted counter: %.2f for order %s", self.agent_id, proposed_price, order_id[:8])
        elif proposed_price >= cost * 0.95:
            # Counter with a middle ground
            middle = (proposed_price + cost * 1.10) / 2
            from mesh.core.messages import CounterOffer
            response = CounterOffer(
                order_id=order_id,
                original_bid_id=payload.get("original_bid_id", ""),
                from_agent=self.agent_id,
                to_agent=payload.get("from_agent", ""),
                round=payload.get("round", 1) + 1,
                proposed_price_per_unit=round(middle, 2),
                justification=f"Counter: minimum viable at {middle:.2f}",
            )
            self.publish(topics.order_counter(order_id), response)
            logger.info("[%s] Counter-counter: %.2f for order %s", self.agent_id, middle, order_id[:8])

    def _handle_bid_accepted(self, payload: dict) -> None:
        """Our bid was accepted — commit and start fulfillment."""
        if payload.get("supplier_id") != self.agent_id:
            return

        order_id = payload.get("order_id", "")
        quantity = payload.get("agreed_quantity", 0)
        price = payload.get("agreed_price_per_unit", 0)

        self._committed_orders[order_id] = {
            "quantity": quantity,
            "price": price,
            "status": "committed",
        }
        self._active_orders += 1

        # Send commit
        commit = OrderCommit(
            order_id=order_id,
            supplier_id=self.agent_id,
            estimated_ready_seconds=random.randint(3, 8),
        )
        self.publish(topics.order_commit(order_id), commit)
        logger.info("[%s] Committed to order %s: %dx%.2f", self.agent_id, order_id[:8], quantity, price)

        # Schedule fulfillment
        timer = threading.Timer(random.uniform(3, 8), self._fulfill_order, args=[order_id])
        timer.daemon = True
        timer.start()

    def _handle_bid_rejected(self, payload: dict) -> None:
        if payload.get("supplier_id") == self.agent_id:
            logger.info("[%s] Bid rejected for order %s", self.agent_id, payload.get("order_id", "")[:8])

    def _fulfill_order(self, order_id: str) -> None:
        """Simulate order fulfillment and request shipping."""
        order_data = self._committed_orders.get(order_id)
        if not order_data:
            return

        # Deduct inventory
        # (simplified — in real scenario we'd track which goods)
        order_data["status"] = "fulfilled"

        # Request shipping
        shipment = ShippingRequest(
            order_id=order_id,
            origin=f"warehouse_{self.agent_id[:4]}",
            destination="buyer_warehouse",
            weight_kg=order_data["quantity"] * 0.5,
            fragile=True,
            deadline_seconds=30,
        )
        self.publish(topics.shipping_request(shipment.shipment_id), shipment)

        status = OrderStatus(order_id=order_id, status="shipping", updated_by=self.agent_id)
        self.publish(topics.order_status(order_id), status)

        logger.info("[%s] Order %s fulfilled, requesting shipping", self.agent_id, order_id[:8])

    def _handle_shipping_confirmed(self, topic: str, payload: dict) -> None:
        order_id = payload.get("order_id", "")
        if order_id in self._committed_orders:
            self._committed_orders[order_id]["status"] = "shipped"
            self._active_orders = max(0, self._active_orders - 1)
