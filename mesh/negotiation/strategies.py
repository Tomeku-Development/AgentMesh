"""Bidding strategies for the negotiation engine."""

from __future__ import annotations

import asyncio
import enum
import logging
from dataclasses import dataclass

from mesh.llm.prompts import negotiation_counter_prompt
from mesh.llm.router import LLMRouter


class StrategyType(str, enum.Enum):
    AGGRESSIVE = "aggressive"      # Low counter-offers, maximize savings
    CONSERVATIVE = "conservative"  # Small adjustments, prioritize deal completion
    ADAPTIVE = "adaptive"          # Adjusts based on market and competition
    LLM = "llm"                    # Uses LLM for dynamic counter-offer computation


@dataclass
class NegotiationContext:
    """Context available to strategies during negotiation."""
    my_role: str  # "buyer" or "supplier"
    original_price: float
    max_price: float  # Buyer's max or supplier's min
    market_price: float
    num_competing_bids: int
    current_round: int
    max_rounds: int
    my_reputation: float
    counterparty_reputation: float


class BiddingStrategy:
    """Base class for bidding strategies."""

    def compute_counter(self, ctx: NegotiationContext, their_price: float) -> float:
        """Compute a counter-offer price given the other party's price."""
        raise NotImplementedError


class AggressiveStrategy(BiddingStrategy):
    """Buyer: push hard for lower prices. Supplier: hold firm."""

    def compute_counter(self, ctx: NegotiationContext, their_price: float) -> float:
        if ctx.my_role == "buyer":
            # Buyer aggressively counters below market
            target = ctx.market_price * 0.90
            # Move 40% from their price toward target
            return their_price - 0.4 * (their_price - target)
        else:
            # Supplier gives minimal discount (5%)
            return their_price * 0.95


class ConservativeStrategy(BiddingStrategy):
    """Small adjustments to maximize deal completion probability."""

    def compute_counter(self, ctx: NegotiationContext, their_price: float) -> float:
        if ctx.my_role == "buyer":
            # Buyer counters 5-10% below their price
            discount = 0.05 + (0.05 * (1 - ctx.current_round / ctx.max_rounds))
            return their_price * (1 - discount)
        else:
            # Supplier gives moderate discount (3%)
            return their_price * 0.97


class AdaptiveStrategy(BiddingStrategy):
    """Adjusts based on market conditions and competition."""

    def compute_counter(self, ctx: NegotiationContext, their_price: float) -> float:
        # More competition = more aggressive
        competition_factor = min(1.0, ctx.num_competing_bids / 5.0)
        # Later rounds = more concessions
        round_pressure = ctx.current_round / ctx.max_rounds

        if ctx.my_role == "buyer":
            # Base discount 5-15% depending on competition and round
            base_discount = 0.05 + 0.10 * competition_factor
            round_concession = 0.03 * round_pressure
            discount = base_discount - round_concession
            return their_price * (1 - max(0.02, discount))
        else:
            # More competitors = more willing to discount
            base_discount = 0.02 + 0.08 * competition_factor
            round_concession = 0.03 * round_pressure
            discount = base_discount + round_concession
            return their_price * (1 - min(0.15, discount))


class LLMStrategy(BiddingStrategy):
    """Uses LLM for dynamic counter-offer computation."""

    def __init__(self, llm_router: LLMRouter):
        self._llm_router = llm_router
        self._fallback = AdaptiveStrategy()
        self._logger = logging.getLogger(__name__)

    def compute_counter(self, ctx: NegotiationContext, their_price: float) -> float:
        try:
            context_dict = {
                "my_role": ctx.my_role,
                "original_price": ctx.original_price,
                "max_price": ctx.max_price,
                "market_price": ctx.market_price,
                "num_competing_bids": ctx.num_competing_bids,
                "current_round": ctx.current_round,
                "max_rounds": ctx.max_rounds,
                "my_reputation": ctx.my_reputation,
                "counterparty_reputation": ctx.counterparty_reputation,
            }
            system_prompt, user_prompt = negotiation_counter_prompt(context_dict, their_price, [])
            result = asyncio.run(self._llm_router.complete_json(user_prompt, system_prompt))
            counter_price = float(result["counter_price"])
            # Safety bounds
            floor = ctx.market_price * 0.80
            ceiling = ctx.max_price
            counter_price = max(floor, min(ceiling, counter_price))
            self._logger.info(
                "LLM negotiation counter: %.2f (raw: %s)",
                counter_price, result.get("reasoning", ""),
            )
            return counter_price
        except Exception as e:
            self._logger.warning("LLM negotiation failed, using adaptive fallback: %s", e)
            return self._fallback.compute_counter(ctx, their_price)


STRATEGY_MAP: dict[StrategyType, type[BiddingStrategy]] = {
    StrategyType.AGGRESSIVE: AggressiveStrategy,
    StrategyType.CONSERVATIVE: ConservativeStrategy,
    StrategyType.ADAPTIVE: AdaptiveStrategy,
}


def get_strategy(
    strategy_type: StrategyType,
    llm_router: LLMRouter | None = None,
) -> BiddingStrategy:
    """Factory to get a strategy instance."""
    if strategy_type == StrategyType.LLM:
        if llm_router is None:
            return AdaptiveStrategy()  # fallback if no router
        return LLMStrategy(llm_router)
    return STRATEGY_MAP[strategy_type]()
