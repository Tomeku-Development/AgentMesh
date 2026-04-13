"""Multi-round negotiation state machine."""

from __future__ import annotations

import asyncio
import enum
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from mesh.core.messages import CounterOffer, SupplierBid
from mesh.llm.prompts import buyer_evaluate_bids_prompt
from mesh.llm.router import LLMDisabledError, LLMProviderError, LLMRouter
from mesh.negotiation.strategies import (
    NegotiationContext,
    StrategyType,
    get_strategy,
)


class NegotiationState(str, enum.Enum):
    COLLECTING_BIDS = "collecting_bids"
    EVALUATING = "evaluating"
    COUNTERING = "countering"
    AWAITING_RESPONSE = "awaiting_response"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"


@dataclass
class NegotiationRound:
    """A single round of counter-offers."""
    round_number: int
    counter_from: str  # agent_id
    counter_to: str
    proposed_price: float
    response_price: float | None = None
    accepted: bool = False
    timestamp: float = field(default_factory=time.time)


@dataclass
class NegotiationSession:
    """Tracks the negotiation for a single order."""
    order_id: str
    buyer_id: str
    max_price: float
    market_price: float
    quality_threshold: float
    bid_deadline: float  # absolute timestamp
    negotiate_deadline: float  # absolute timestamp
    max_rounds: int = 3

    state: NegotiationState = NegotiationState.COLLECTING_BIDS
    bids: list[SupplierBid] = field(default_factory=list)
    rounds: list[NegotiationRound] = field(default_factory=list)
    winner_bid_id: str | None = None
    winner_supplier_id: str | None = None
    agreed_price: float | None = None

    def add_bid(self, bid: SupplierBid) -> None:
        """Record a supplier bid."""
        self.bids.append(bid)

    @property
    def current_round(self) -> int:
        return len(self.rounds)

    @property
    def is_expired(self) -> bool:
        return time.time() > self.negotiate_deadline

    @property
    def can_counter(self) -> bool:
        return (
            self.current_round < self.max_rounds
            and not self.is_expired
            and self.state in {NegotiationState.EVALUATING, NegotiationState.COUNTERING}
        )


class NegotiationEngine:
    """Manages negotiation sessions for orders.

    The engine evaluates bids using reputation-weighted scoring,
    decides whether to accept or counter, and tracks the multi-round process.
    """

    def __init__(
        self,
        strategy_type: StrategyType = StrategyType.ADAPTIVE,
        llm_router: LLMRouter | None = None,
    ) -> None:
        self._sessions: dict[str, NegotiationSession] = {}
        self._llm_router = llm_router
        self._strategy = get_strategy(strategy_type, llm_router)
        self._logger = logging.getLogger(__name__)

    def create_session(
        self,
        order_id: str,
        buyer_id: str,
        max_price: float,
        market_price: float,
        quality_threshold: float,
        bid_window: float,
        negotiate_window: float,
        max_rounds: int = 3,
    ) -> NegotiationSession:
        """Create a new negotiation session for an order."""
        now = time.time()
        session = NegotiationSession(
            order_id=order_id,
            buyer_id=buyer_id,
            max_price=max_price,
            market_price=market_price,
            quality_threshold=quality_threshold,
            bid_deadline=now + bid_window,
            negotiate_deadline=now + bid_window + negotiate_window,
            max_rounds=max_rounds,
        )
        self._sessions[order_id] = session
        return session

    def get_session(self, order_id: str) -> NegotiationSession | None:
        return self._sessions.get(order_id)

    def evaluate_bids(
        self,
        order_id: str,
        score_fn: Any = None,
    ) -> tuple[SupplierBid | None, bool]:
        """Evaluate collected bids. Returns (best_bid, should_counter).

        Args:
            order_id: The order to evaluate bids for.
            score_fn: Optional callable(bid) -> float for custom scoring.

        Returns:
            (best_bid, should_counter): best_bid is None if no bids.
            should_counter is True if we should negotiate rather than accept.
        """
        session = self._sessions.get(order_id)
        if not session or not session.bids:
            return None, False

        session.state = NegotiationState.EVALUATING

        # Try LLM-based evaluation if router is available
        if self._llm_router is not None:
            try:
                bids_data = [
                    {
                        "bid_id": bid.bid_id,
                        "supplier_id": bid.supplier_id,
                        "price_per_unit": bid.price_per_unit,
                        "reputation_score": bid.reputation_score,
                        "estimated_fulfillment_seconds": bid.estimated_fulfillment_seconds,
                    }
                    for bid in session.bids
                ]
                system_prompt, user_prompt = buyer_evaluate_bids_prompt(
                    bids_data,
                    session.market_price,
                    session.max_price,
                    session.quality_threshold,
                )
                result = asyncio.run(self._llm_router.complete_json(user_prompt, system_prompt))

                # Parse result - expect {ranked_bids, should_counter, reasoning}
                ranked_bids = result.get("ranked_bids", [])
                should_counter = result.get("should_counter", False)

                # Validate bid_ids and scores
                valid_bids = {bid.bid_id: bid for bid in session.bids}
                for ranked in ranked_bids:
                    bid_id = ranked.get("bid_id")
                    score = ranked.get("score")
                    if bid_id in valid_bids and isinstance(score, (int, float)):
                        best_bid = valid_bids[bid_id]
                        self._logger.info(
                            "LLM bid evaluation: selected %s with score %.2f (%s)",
                            bid_id,
                            float(score),
                            ranked.get("reasoning", ""),
                        )
                        return best_bid, should_counter

                self._logger.warning("LLM evaluation returned no valid bids, falling back")
            except (LLMDisabledError, LLMProviderError, ValueError, KeyError) as e:
                self._logger.warning(
                    "LLM bid evaluation failed, "
                    "using deterministic fallback: %s", e,
                )
            except Exception as e:
                self._logger.warning("LLM bid evaluation error: %s", e)

        # Fallback: Score and sort bids deterministically
        if score_fn:
            scored = [(score_fn(bid), bid) for bid in session.bids]
        else:
            scored = [(self._default_score(bid, session), bid) for bid in session.bids]

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_bid = scored[0]

        # Decision: accept directly or counter?
        if best_bid.price_per_unit <= session.market_price * 0.95:
            # Great price — accept immediately
            return best_bid, False
        elif best_bid.price_per_unit <= session.max_price:
            # Acceptable but could be better — try to counter
            return best_bid, session.can_counter
        else:
            # Over budget — must counter or reject
            return best_bid, session.can_counter

    def generate_counter(
        self,
        order_id: str,
        target_bid: SupplierBid,
        my_reputation: float = 0.5,
        counterparty_reputation: float = 0.5,
    ) -> CounterOffer | None:
        """Generate a counter-offer for a bid."""
        session = self._sessions.get(order_id)
        if not session or not session.can_counter:
            return None

        ctx = NegotiationContext(
            my_role="buyer",
            original_price=target_bid.price_per_unit,
            max_price=session.max_price,
            market_price=session.market_price,
            num_competing_bids=len(session.bids),
            current_round=session.current_round + 1,
            max_rounds=session.max_rounds,
            my_reputation=my_reputation,
            counterparty_reputation=counterparty_reputation,
        )

        counter_price = self._strategy.compute_counter(ctx, target_bid.price_per_unit)
        counter_price = max(counter_price, session.market_price * 0.80)  # Floor

        session.state = NegotiationState.COUNTERING
        round_entry = NegotiationRound(
            round_number=session.current_round + 1,
            counter_from=session.buyer_id,
            counter_to=target_bid.supplier_id,
            proposed_price=counter_price,
        )
        session.rounds.append(round_entry)

        return CounterOffer(
            order_id=order_id,
            original_bid_id=target_bid.bid_id,
            from_agent=session.buyer_id,
            to_agent=target_bid.supplier_id,
            round=round_entry.round_number,
            proposed_price_per_unit=round(counter_price, 2),
            proposed_quantity=target_bid.available_quantity,
            justification=(
                f"Market price is {session.market_price:.2f}; "
                f"round {round_entry.round_number}"
                f"/{session.max_rounds}"
            ),
        )

    def process_counter_response(
        self,
        order_id: str,
        from_supplier: str,
        response_price: float,
        accepted: bool,
    ) -> None:
        """Process a supplier's response to our counter-offer."""
        session = self._sessions.get(order_id)
        if not session or not session.rounds:
            return

        last_round = session.rounds[-1]
        last_round.response_price = response_price
        last_round.accepted = accepted

        if accepted:
            session.state = NegotiationState.ACCEPTED
            session.agreed_price = response_price
            for bid in session.bids:
                if bid.supplier_id == from_supplier:
                    session.winner_bid_id = bid.bid_id
                    session.winner_supplier_id = from_supplier
                    break

    def accept_bid(self, order_id: str, bid: SupplierBid) -> None:
        """Directly accept a bid without countering."""
        session = self._sessions.get(order_id)
        if not session:
            return
        session.state = NegotiationState.ACCEPTED
        session.winner_bid_id = bid.bid_id
        session.winner_supplier_id = bid.supplier_id
        session.agreed_price = bid.price_per_unit

    def timeout_session(self, order_id: str) -> None:
        """Mark a session as timed out."""
        session = self._sessions.get(order_id)
        if session:
            session.state = NegotiationState.TIMED_OUT

    def _default_score(self, bid: SupplierBid, session: NegotiationSession) -> float:
        """Default bid scoring using price and reputation."""
        price_score = max(0, 1.0 - (bid.price_per_unit / session.max_price))
        rep_score = bid.reputation_score
        return 0.5 * price_score + 0.5 * rep_score
