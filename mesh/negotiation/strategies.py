"""Bidding strategies for the negotiation engine."""

from __future__ import annotations

import enum
import random
from dataclasses import dataclass


class StrategyType(str, enum.Enum):
    AGGRESSIVE = "aggressive"      # Low counter-offers, maximize savings
    CONSERVATIVE = "conservative"  # Small adjustments, prioritize deal completion
    ADAPTIVE = "adaptive"          # Adjusts based on market and competition


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


STRATEGY_MAP: dict[StrategyType, type[BiddingStrategy]] = {
    StrategyType.AGGRESSIVE: AggressiveStrategy,
    StrategyType.CONSERVATIVE: ConservativeStrategy,
    StrategyType.ADAPTIVE: AdaptiveStrategy,
}


def get_strategy(strategy_type: StrategyType) -> BiddingStrategy:
    """Factory to get a strategy instance."""
    return STRATEGY_MAP[strategy_type]()
