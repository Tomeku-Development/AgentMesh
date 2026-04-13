"""SupplierAgent — manages inventory, bids on orders, fulfills commitments."""

from __future__ import annotations

import asyncio
import logging
import random
import threading

from mesh.agents.base import BaseAgent
from mesh.core import topics
from mesh.core.capability_utils import normalize_capability
from mesh.core.messages import (
    MessageEnvelope,
    OrderCommit,
    OrderStatus,
    ShippingRequest,
    SupplierBid,
)
from mesh.llm.prompts import supplier_bid_prompt, supplier_counter_prompt
from mesh.llm.router import LLMDisabledError, LLMProviderError, LLMRouter
from mesh.negotiation.strategies import (
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
        self._llm_router = LLMRouter(config)

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

        # Check if we can fulfill (case-insensitive matching)
        normalized_category = normalize_capability(category)
        normalized_caps = {normalize_capability(c) for c in self.capabilities}
        normalized_required = [normalize_capability(c) for c in required_caps]
        if normalized_category not in normalized_caps and not any(
            c in normalized_caps for c in normalized_required
        ):
            return

        available = self._inventory.get(goods, 0)
        if available <= 0:
            return

        # Calculate bid price with LLM enhancement
        cost = self._base_costs.get(goods, max_price * 0.7)
        market = self._market_prices.get(goods, max_price * 0.9)

        # Get our reputation for this category
        rep_score = self.reputation.get_score(self.agent_id, category)

        # Try LLM first for pricing decision
        bid_price = None
        fulfillment_seconds = None
        llm_used = False

        try:
            system_prompt, user_prompt = supplier_bid_prompt(
                goods=goods,
                cost=cost,
                market_price=market,
                inventory=available,
                active_orders=self._active_orders,
                quantity_requested=quantity,
                max_price=max_price,
                reputation=rep_score,
            )
            result = asyncio.run(self._llm_router.complete_json(user_prompt, system_prompt))

            # Parse LLM response
            should_bid = result.get("accept", result.get("should_bid", True))
            if should_bid is False:
                logger.info("[%s] LLM advised not to bid on order %s", self.agent_id, order_id[:8])
                return

            bid_price = result.get("bid_price")
            fulfillment_seconds = result.get("estimated_delivery_epochs",
                                             result.get("fulfillment_estimate_seconds"))

            # Validate LLM output
            min_price = cost * 0.90  # Don't go below near-cost
            if (bid_price is not None and bid_price > 0
                    and bid_price <= max_price
                    and bid_price >= min_price):
                llm_used = True
                logger.info(
                    "[%s] LLM pricing for order %s: %.2f/unit (reasoning: %s)",
                    self.agent_id, order_id[:8], bid_price, result.get("reasoning", "N/A")[:50]
                )
            else:
                logger.warning(
                    "[%s] LLM bid_price %.2f invalid (cost=%.2f, max=%.2f), using fallback",
                    self.agent_id, bid_price, cost, max_price
                )
                bid_price = None
        except (LLMDisabledError, LLMProviderError, Exception) as e:
            logger.warning(
                "[%s] LLM failed for bid pricing: %s, "
                "using fallback",
                self.agent_id, str(e)[:100],
            )

        # Fallback to original logic if LLM didn't provide valid price
        if bid_price is None:
            margin = random.uniform(0.05, 0.15)
            bid_price = cost * (1 + margin)

            # Don't bid above max price
            if bid_price > max_price:
                bid_price = max_price * random.uniform(0.90, 0.98)

        if fulfillment_seconds is None:
            fulfillment_seconds = random.randint(5, 15)

        bid = SupplierBid(
            order_id=order_id,
            supplier_id=self.agent_id,
            price_per_unit=round(bid_price, 2),
            available_quantity=min(available, quantity),
            estimated_fulfillment_seconds=fulfillment_seconds,
            reputation_score=rep_score,
            notes=f"From {self.agent_id[:8]}, {available} in stock",
        )

        self.publish(topics.order_bid(order_id), bid)
        logger.info(
            "[%s] Bid on order %s: %.2f/unit x%d (LLM: %s)",
            self.agent_id, order_id[:8], bid_price, min(available, quantity), llm_used,
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
        market = self._market_prices.get(goods_category, proposed_price)
        round_num = payload.get("round", 1)

        # Try LLM first for counter-offer decision
        action = None
        counter_price = None
        llm_used = False

        try:
            system_prompt, user_prompt = supplier_counter_prompt(
                proposed_price=proposed_price,
                cost=cost,
                market_price=market,
                reputation=self.reputation.get_score(self.agent_id, goods_category),
                round_num=round_num,
            )
            result = asyncio.run(self._llm_router.complete_json(user_prompt, system_prompt))

            action = result.get(
                "action",
                "counter" if not result.get("accept", False)
                else "accept",
            )
            counter_price = result.get("counter_price")
            llm_used = True
            logger.info(
                "[%s] LLM counter decision for order %s: %s (reasoning: %s)",
                self.agent_id, order_id[:8], action, result.get("reasoning", "N/A")[:50]
            )
        except (LLMDisabledError, LLMProviderError, Exception) as e:
            logger.warning(
                "[%s] LLM failed for counter-offer: %s, "
                "using fallback",
                self.agent_id, str(e)[:100],
            )

        from mesh.core.messages import CounterOffer

        # Process LLM decision or use fallback logic
        if llm_used and action:
            if action == "accept":
                # Validate: never accept below cost * 0.90
                if proposed_price >= cost * 0.90:
                    response = CounterOffer(
                        order_id=order_id,
                        original_bid_id=payload.get("original_bid_id", ""),
                        from_agent=self.agent_id,
                        to_agent=payload.get("from_agent", ""),
                        round=round_num,
                        proposed_price_per_unit=proposed_price,
                        justification="Accepted counter-offer (LLM)",
                    )
                    self.publish(topics.order_counter(order_id), response)
                    logger.info(
                        "[%s] Accepted counter (LLM): "
                        "%.2f for order %s",
                        self.agent_id, proposed_price,
                        order_id[:8],
                    )
                    return
                else:
                    logger.warning(
                        "[%s] LLM accept rejected: price %.2f "
                        "below safety floor %.2f",
                        self.agent_id, proposed_price,
                        cost * 0.90,
                    )

            elif action == "counter" and counter_price is not None:
                # Validate counter_price: must be > cost * 0.95 and <= proposed_price * 1.5
                min_counter = cost * 0.95
                max_counter = proposed_price * 1.5
                if min_counter <= counter_price <= max_counter:
                    response = CounterOffer(
                        order_id=order_id,
                        original_bid_id=payload.get("original_bid_id", ""),
                        from_agent=self.agent_id,
                        to_agent=payload.get("from_agent", ""),
                        round=round_num + 1,
                        proposed_price_per_unit=round(counter_price, 2),
                        justification=f"Counter (LLM): {counter_price:.2f}",
                    )
                    self.publish(topics.order_counter(order_id), response)
                    logger.info(
                        "[%s] Counter-counter (LLM): "
                        "%.2f for order %s",
                        self.agent_id, counter_price,
                        order_id[:8],
                    )
                    return
                else:
                    logger.warning(
                        "[%s] LLM counter_price %.2f out of bounds [%.2f, %.2f], using fallback",
                        self.agent_id, counter_price, min_counter, max_counter
                    )

            elif action == "reject":
                logger.info(
                    "[%s] Rejected counter-offer (LLM) "
                    "for order %s",
                    self.agent_id, order_id[:8],
                )
                return

        # Fallback to original logic
        if proposed_price >= cost * 1.05:
            # Accept — still profitable
            response = CounterOffer(
                order_id=order_id,
                original_bid_id=payload.get("original_bid_id", ""),
                from_agent=self.agent_id,
                to_agent=payload.get("from_agent", ""),
                round=round_num,
                proposed_price_per_unit=proposed_price,
                justification="Accepted counter-offer",
            )
            self.publish(topics.order_counter(order_id), response)
            logger.info(
                "[%s] Accepted counter: %.2f for order %s",
                self.agent_id, proposed_price, order_id[:8],
            )
        elif proposed_price >= cost * 0.95:
            # Counter with a middle ground
            middle = (proposed_price + cost * 1.10) / 2
            response = CounterOffer(
                order_id=order_id,
                original_bid_id=payload.get("original_bid_id", ""),
                from_agent=self.agent_id,
                to_agent=payload.get("from_agent", ""),
                round=round_num + 1,
                proposed_price_per_unit=round(middle, 2),
                justification=f"Counter: minimum viable at {middle:.2f}",
            )
            self.publish(topics.order_counter(order_id), response)
            logger.info(
                "[%s] Counter-counter: %.2f for order %s",
                self.agent_id, middle, order_id[:8],
            )

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
        logger.info(
            "[%s] Committed to order %s: %dx%.2f",
            self.agent_id, order_id[:8], quantity, price,
        )

        # Schedule fulfillment
        timer = threading.Timer(random.uniform(3, 8), self._fulfill_order, args=[order_id])
        timer.daemon = True
        timer.start()

    def _handle_bid_rejected(self, payload: dict) -> None:
        if payload.get("supplier_id") == self.agent_id:
            logger.info(
                "[%s] Bid rejected for order %s",
                self.agent_id,
                payload.get("order_id", "")[:8],
            )

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
