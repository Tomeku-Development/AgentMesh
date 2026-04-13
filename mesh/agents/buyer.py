"""BuyerAgent — creates purchase orders and manages the buy-side of negotiations."""

from __future__ import annotations

import asyncio
import logging
import threading

from mesh.agents.base import BaseAgent
from mesh.core import topics
from mesh.core.messages import (
    BidAcceptance,
    BidRejection,
    InspectionRequest,
    MessageEnvelope,
    OrderStatus,
    PurchaseOrderRequest,
    SupplierBid,
)
from mesh.llm.prompts import buyer_evaluate_bids_prompt, buyer_settlement_prompt
from mesh.llm.router import LLMDisabledError, LLMProviderError, LLMRouter
from mesh.negotiation.engine import NegotiationEngine

logger = logging.getLogger(__name__)


class BuyerAgent(BaseAgent):
    """Creates purchase orders, evaluates bids, negotiates prices, manages escrow."""

    def __init__(self, config, identity=None, ledger=None, reputation=None):
        config.agent_role = "buyer"
        super().__init__(config, identity, ledger, reputation)
        self.negotiation = NegotiationEngine()
        self._pending_orders: dict[str, PurchaseOrderRequest] = {}
        self._order_timers: dict[str, threading.Timer] = {}
        self._market_prices: dict[str, float] = {}
        self._llm_router = LLMRouter(config)

    def _subscribe_topics(self) -> None:
        self.transport.subscribe("mesh/orders/+/bid", qos=1)
        self.transport.subscribe("mesh/orders/+/counter", qos=1)
        self.transport.subscribe("mesh/orders/+/commit", qos=1)
        self.transport.subscribe("mesh/shipping/+/deliver", qos=1)
        self.transport.subscribe("mesh/quality/+/report", qos=1)
        self.transport.subscribe(topics.MARKET_PRICES, qos=1)

    def _handle_message(self, topic: str, envelope: MessageEnvelope) -> None:
        payload = envelope.payload

        if topic == topics.MARKET_PRICES:
            self._handle_market_prices(payload)
        elif "/bid" in topic and "shipping" not in topic:
            self._handle_supplier_bid(topic, payload)
        elif "/commit" in topic:
            self._handle_order_commit(topic, payload)
        elif "/deliver" in topic:
            self._handle_delivery(topic, payload)
        elif "/report" in topic:
            self._handle_inspection_report(topic, payload)
        elif "/counter" in topic:
            self._handle_counter_response(topic, payload)

    def _handle_market_prices(self, payload: dict) -> None:
        prices = payload.get("prices", {})
        for goods, data in prices.items():
            self._market_prices[goods] = data.get("price", 0)

    def create_order(
        self,
        goods: str,
        category: str,
        quantity: int,
        max_price_per_unit: float,
        quality_threshold: float = 0.85,
        delivery_deadline_seconds: int = 60,
    ) -> str:
        """Create and publish a purchase order."""
        po = PurchaseOrderRequest(
            goods=goods,
            category=category,
            quantity=quantity,
            max_price_per_unit=max_price_per_unit,
            quality_threshold=quality_threshold,
            delivery_deadline_seconds=delivery_deadline_seconds,
            required_capabilities=[category],
            bid_deadline_seconds=int(self.config.bid_window),
        )

        self._pending_orders[po.order_id] = po
        self._active_orders += 1

        # Create negotiation session
        market_price = self._market_prices.get(goods, max_price_per_unit * 0.9)
        self.negotiation.create_session(
            order_id=po.order_id,
            buyer_id=self.agent_id,
            max_price=max_price_per_unit,
            market_price=market_price,
            quality_threshold=quality_threshold,
            bid_window=self.config.bid_window,
            negotiate_window=self.config.negotiate_window,
            max_rounds=self.config.negotiate_max_rounds,
        )

        # Publish order
        self.publish(topics.order_request(po.order_id), po)

        # Update status
        status = OrderStatus(
            order_id=po.order_id, status="bidding", updated_by=self.agent_id
        )
        self.publish(topics.order_status(po.order_id), status)

        # Schedule bid evaluation after bid window
        timer = threading.Timer(self.config.bid_window, self._evaluate_bids, args=[po.order_id])
        timer.daemon = True
        timer.start()
        self._order_timers[po.order_id] = timer

        logger.info(
            "[%s] Created order %s: %dx %s @ max %.2f",
            self.agent_id, po.order_id[:8], quantity, goods, max_price_per_unit,
        )
        return po.order_id

    def _handle_supplier_bid(self, topic: str, payload: dict) -> None:
        bid = SupplierBid(**payload)
        session = self.negotiation.get_session(bid.order_id)
        if session:
            session.add_bid(bid)
            logger.info(
                "[%s] Received bid from %s for order %s: %.2f/unit",
                self.agent_id, bid.supplier_id[:8], bid.order_id[:8], bid.price_per_unit,
            )

    def _evaluate_bids(self, order_id: str) -> None:
        """Evaluate collected bids after the bid window closes."""
        session = self.negotiation.get_session(order_id)
        if not session or not session.bids:
            logger.warning("[%s] No bids for order %s", self.agent_id, order_id[:8])
            self._cancel_order(order_id, "No bids received")
            return

        # Try LLM-based bid evaluation first
        best_bid = None
        should_counter = False
        llm_evaluated = False

        try:
            # Build bids data for LLM
            bids_data = []
            for bid in session.bids:
                rep_score = self.reputation.get_score(
                    bid.supplier_id,
                    self._pending_orders[order_id].category
                    if order_id in self._pending_orders else "",
                )
                bids_data.append({
                    "bid_id": bid.bid_id,
                    "supplier_id": bid.supplier_id,
                    "price_per_unit": bid.price_per_unit,
                    "reputation_score": rep_score,
                    "estimated_fulfillment_seconds": bid.estimated_fulfillment_seconds,
                    "available_quantity": bid.available_quantity,
                })

            market_price = self._market_prices.get(
                self._pending_orders[order_id].goods if order_id in self._pending_orders else "",
                session.max_price * 0.9,
            )

            system_prompt, user_prompt = buyer_evaluate_bids_prompt(
                bids=bids_data,
                market_price=market_price,
                max_price=session.max_price,
                quality_threshold=session.quality_threshold,
            )

            result = asyncio.run(
                self._llm_router.complete_json(user_prompt, system_prompt)
            )

            # Parse LLM result
            ranked_bids = result.get("ranked_bids", [])
            llm_should_counter = result.get("should_counter", False)

            if ranked_bids and len(ranked_bids) > 0:
                # Find the best bid by matching bid_id
                best_bid_id = ranked_bids[0].get("bid_id")
                for bid in session.bids:
                    if bid.bid_id == best_bid_id:
                        best_bid = bid
                        should_counter = llm_should_counter
                        llm_evaluated = True
                        logger.info(
                            "[%s] LLM evaluated bids for order %s: "
                            "selected %s (score: %.2f, reasoning: %s)",
                            self.agent_id, order_id[:8], best_bid_id[:8],
                            ranked_bids[0].get("score", 0),
                            ranked_bids[0].get("reasoning", "N/A")[:50],
                        )
                        break

        except (LLMDisabledError, LLMProviderError, Exception) as e:
            logger.warning("[%s] LLM bid evaluation failed, using fallback: %s", self.agent_id, e)

        # Fallback to original scoring if LLM didn't work
        if not llm_evaluated:
            def score_fn(bid):
                rep_score = self.reputation.get_score(
                    bid.supplier_id,
                    self._pending_orders[order_id].category
                    if order_id in self._pending_orders else "",
                )
                return self.reputation.score_bid(
                    price=bid.price_per_unit,
                    max_price=session.max_price,
                    reputation=rep_score,
                    estimated_time=bid.estimated_fulfillment_seconds,
                    deadline=self._pending_orders.get(
                        order_id,
                        PurchaseOrderRequest(
                            goods="", category="",
                            quantity=0, max_price_per_unit=0,
                        ),
                    ).delivery_deadline_seconds,
                    confidence=0.5,
                )

            best_bid, should_counter = self.negotiation.evaluate_bids(order_id, score_fn)

        if not best_bid:
            self._cancel_order(order_id, "No valid bids")
            return

        if should_counter and session.can_counter:
            # Try negotiation
            counter = self.negotiation.generate_counter(order_id, best_bid)
            if counter:
                status = OrderStatus(
                    order_id=order_id, status="negotiating", updated_by=self.agent_id
                )
                self.publish(topics.order_status(order_id), status)
                self.publish(topics.order_counter(order_id), counter)
                logger.info(
                    "[%s] Counter-offer to %s: %.2f/unit (was %.2f)",
                    self.agent_id, best_bid.supplier_id[:8],
                    counter.proposed_price_per_unit, best_bid.price_per_unit,
                )
                # Schedule timeout for counter response
                timer = threading.Timer(
                    self.config.negotiate_window,
                    self._finalize_negotiation,
                    args=[order_id],
                )
                timer.daemon = True
                timer.start()
                self._order_timers[order_id] = timer
                return

        # Accept best bid directly
        self._accept_bid(order_id, best_bid)

    def _handle_counter_response(self, topic: str, payload: dict) -> None:
        """Handle supplier's response to our counter-offer."""
        order_id = payload.get("order_id", "")
        from_agent = payload.get("from_agent", "")
        proposed_price = payload.get("proposed_price_per_unit", 0)
        session = self.negotiation.get_session(order_id)

        if not session:
            return

        # If this is a supplier counter-counter, decide whether to accept
        accept = False

        # Try LLM-based decision
        try:
            market_price = self._market_prices.get(
                self._pending_orders[order_id].goods if order_id in self._pending_orders else "",
                session.max_price * 0.9,
            )
            # Build context for LLM
            context = {
                "role": "buyer",
                "target_price": session.max_price,
                "round": session.current_round if hasattr(session, "current_round") else 1,
                "max_rounds": self.config.negotiate_max_rounds,
            }

            from mesh.llm.prompts import negotiation_counter_prompt
            system_prompt, user_prompt = negotiation_counter_prompt(
                context=context,
                their_price=proposed_price,
                market_history=[market_price] if market_price else [session.max_price * 0.9],
            )

            result = asyncio.run(
                self._llm_router.complete_json(user_prompt, system_prompt)
            )

            llm_accept = result.get("accept", False)
            reasoning = result.get("reasoning", "")

            # If LLM says accept, or safety override (price is really good)
            if llm_accept:
                accept = True
                logger.info(
                    "[%s] LLM accepted counter-counter for order %s: %.2f (reasoning: %s)",
                    self.agent_id, order_id[:8], proposed_price, reasoning[:50],
                )
            elif proposed_price <= session.max_price * 0.98:
                # Safety override: price is close enough to max, accept anyway
                accept = True
                logger.info(
                    "[%s] LLM rejected but safety override for order %s: %.2f <= %.2f",
                    self.agent_id, order_id[:8], proposed_price, session.max_price * 0.98,
                )
            else:
                logger.info(
                    "[%s] LLM rejected counter-counter for order %s: %.2f (reasoning: %s)",
                    self.agent_id, order_id[:8], proposed_price, reasoning[:50],
                )

        except (LLMDisabledError, LLMProviderError, Exception) as e:
            logger.warning("[%s] LLM counter decision failed, using fallback: %s", self.agent_id, e)
            # Fallback to original logic
            accept = proposed_price <= session.max_price

        if accept:
            # Accept this counter
            for bid in session.bids:
                if bid.supplier_id == from_agent:
                    bid.price_per_unit = proposed_price
                    self._accept_bid(order_id, bid)
                    return

    def _finalize_negotiation(self, order_id: str) -> None:
        """Called when negotiation window expires — accept best available."""
        session = self.negotiation.get_session(order_id)
        if not session or session.winner_bid_id:
            return
        # Accept the best bid we have
        if session.bids:
            best = min(session.bids, key=lambda b: b.price_per_unit)
            self._accept_bid(order_id, best)

    def _accept_bid(self, order_id: str, bid: SupplierBid) -> None:
        """Accept a bid and lock escrow."""
        po = self._pending_orders.get(order_id)
        if not po:
            return

        self.negotiation.accept_bid(order_id, bid)
        agreed_qty = min(bid.available_quantity, po.quantity)
        escrow_amount = bid.price_per_unit * agreed_qty + 20  # +20 for shipping+inspection buffer

        try:
            self.ledger.escrow_lock(self.agent_id, escrow_amount, order_id)
        except Exception as e:
            logger.error("[%s] Escrow lock failed: %s", self.agent_id, e)
            self._cancel_order(order_id, f"Insufficient funds: {e}")
            return

        acceptance = BidAcceptance(
            order_id=order_id,
            accepted_bid_id=bid.bid_id,
            supplier_id=bid.supplier_id,
            agreed_price_per_unit=bid.price_per_unit,
            agreed_quantity=agreed_qty,
            escrow_amount=escrow_amount,
        )
        self.publish(topics.order_accept(order_id), acceptance)

        # Reject other bidders
        for other in self.negotiation.get_session(order_id).bids:
            if other.bid_id != bid.bid_id:
                rejection = BidRejection(
                    order_id=order_id,
                    rejected_bid_id=other.bid_id,
                    supplier_id=other.supplier_id,
                    reason="Another bid was accepted",
                )
                self.publish(topics.order_reject(order_id), rejection)

        status = OrderStatus(order_id=order_id, status="committed", updated_by=self.agent_id)
        self.publish(topics.order_status(order_id), status)

        logger.info(
            "[%s] Accepted bid from %s: %dx%.2f = %.2f (escrow: %.2f)",
            self.agent_id, bid.supplier_id[:8], agreed_qty,
            bid.price_per_unit, agreed_qty * bid.price_per_unit, escrow_amount,
        )

    def _handle_order_commit(self, topic: str, payload: dict) -> None:
        order_id = payload.get("order_id", "")
        logger.info("[%s] Supplier committed to order %s", self.agent_id, order_id[:8])
        status = OrderStatus(order_id=order_id, status="fulfilling", updated_by=self.agent_id)
        self.publish(topics.order_status(order_id), status)

    def _handle_delivery(self, topic: str, payload: dict) -> None:
        """Delivery received — request quality inspection."""
        shipment_id = payload.get("shipment_id", "")
        order_id = payload.get("order_id", "")
        po = self._pending_orders.get(order_id)
        if not po:
            return

        logger.info("[%s] Delivery received for order %s", self.agent_id, order_id[:8])

        inspection = InspectionRequest(
            order_id=order_id,
            shipment_id=shipment_id,
            goods=po.goods,
            quantity_expected=po.quantity,
            quality_threshold=po.quality_threshold,
        )
        self.publish(topics.quality_request(inspection.inspection_id), inspection)

        status = OrderStatus(order_id=order_id, status="inspecting", updated_by=self.agent_id)
        self.publish(topics.order_status(order_id), status)

    def _handle_inspection_report(self, topic: str, payload: dict) -> None:
        """Process inspection results and settle."""
        order_id = payload.get("order_id", "")
        passed = payload.get("passed", False)
        quality_score = payload.get("quality_score", 0)
        quantity_verified = payload.get("quantity_verified", 0)
        inspector_id = payload.get("inspector_id", "")
        po = self._pending_orders.get(order_id)
        session = self.negotiation.get_session(order_id)

        if not po or not session or not session.winner_supplier_id:
            return

        agreed_price = session.agreed_price or 0
        supplier_id = session.winner_supplier_id

        if passed or payload.get("recommendation") == "partial_accept":
            # Settlement: pay supplier, logistics, inspector
            # Default values (fallback)
            supplier_percentage = 0.92
            inspector_fee = 5.0
            burn_percentage = 0.03
            logistics_fee = 15.0

            # Try LLM-based settlement calculation
            try:
                system_prompt, user_prompt = buyer_settlement_prompt(
                    agreed_price=agreed_price,
                    quantity=quantity_verified,
                    quality_score=quality_score,
                    on_time=True,  # Assuming on-time for now
                )

                result = asyncio.run(
                    self._llm_router.complete_json(user_prompt, system_prompt)
                )

                # Extract and validate LLM values
                llm_supplier_pct = result.get("supplier_percentage", supplier_percentage)
                llm_inspector_fee = result.get("inspector_fee", inspector_fee)
                llm_burn_pct = result.get("burn_percentage", burn_percentage)
                llm_logistics_fee = result.get("logistics_fee", logistics_fee)

                # Validate bounds
                if 0.80 <= llm_supplier_pct <= 0.95:
                    supplier_percentage = llm_supplier_pct
                if 1.0 <= llm_inspector_fee <= 20.0:
                    inspector_fee = llm_inspector_fee
                if 0.01 <= llm_burn_pct <= 0.10:
                    burn_percentage = llm_burn_pct
                if 5.0 <= llm_logistics_fee <= 50.0:
                    logistics_fee = llm_logistics_fee

                logger.info(
                    "[%s] LLM settlement for order %s: "
                    "supplier_pct=%.2f, inspector=%.2f, "
                    "burn_pct=%.3f, reasoning=%s",
                    self.agent_id, order_id[:8],
                    supplier_percentage, inspector_fee,
                    burn_percentage,
                    result.get("reasoning", "N/A")[:50],
                )

            except (LLMDisabledError, LLMProviderError, Exception) as e:
                logger.warning("[%s] LLM settlement failed, using defaults: %s", self.agent_id, e)

            # Calculate final amounts
            supplier_payment = agreed_price * quantity_verified * supplier_percentage
            burn_amount = agreed_price * quantity_verified * burn_percentage

            try:
                self.ledger.escrow_release(order_id, [
                    (supplier_id, supplier_payment, "Order fulfillment payment"),
                    (inspector_id, inspector_fee, "Inspection fee"),
                    (self.ledger.BURN_ADDRESS, burn_amount, "Platform fee (burned)"),
                ])
            except Exception as e:
                logger.error("[%s] Settlement failed: %s", self.agent_id, e)

            # Update reputation
            self.reputation.record_success(
                supplier_id, po.category,
                on_time=True, quality_score=quality_score, order_id=order_id
            )

            status = OrderStatus(order_id=order_id, status="settled", updated_by=self.agent_id)
            self.publish(topics.order_status(order_id), status)
            logger.info(
                "[%s] Order %s settled: paid %.2f to %s",
                self.agent_id, order_id[:8], supplier_payment, supplier_id[:8],
            )
        else:
            # Refund
            try:
                self.ledger.escrow_refund(order_id)
            except Exception as e:
                logger.error("[%s] Refund failed: %s", self.agent_id, e)

            self.reputation.record_failure(supplier_id, po.category, "quality_fail", order_id)
            status = OrderStatus(order_id=order_id, status="failed", updated_by=self.agent_id)
            self.publish(topics.order_status(order_id), status)
            logger.warning("[%s] Order %s failed inspection", self.agent_id, order_id[:8])

        self._active_orders = max(0, self._active_orders - 1)

    def _cancel_order(self, order_id: str, reason: str) -> None:
        status = OrderStatus(
            order_id=order_id, status="cancelled", updated_by=self.agent_id, details=reason
        )
        self.publish(topics.order_status(order_id), status)
        self._active_orders = max(0, self._active_orders - 1)
        logger.info("[%s] Cancelled order %s: %s", self.agent_id, order_id[:8], reason)
