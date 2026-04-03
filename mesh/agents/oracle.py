"""MarketOracleAgent — publishes price feeds and demand forecasts."""

from __future__ import annotations

import logging
import random
import time
import threading

from mesh.agents.base import BaseAgent
from mesh.core.messages import MarketDemand, MarketPriceUpdate, MessageEnvelope
from mesh.core.topics import MARKET_DEMAND, MARKET_PRICES

logger = logging.getLogger(__name__)


class OracleAgent(BaseAgent):
    """Publishes market data (prices, demand) that other agents use for decisions.

    The oracle is a passive agent — it doesn't participate in orders,
    it just provides shared economic context to the mesh.
    """

    def __init__(self, config, identity=None, ledger=None, reputation=None):
        config.agent_role = "oracle"
        super().__init__(config, identity, ledger, reputation)
        self._epoch = 0
        self._base_prices: dict[str, float] = {}
        self._price_thread: threading.Thread | None = None

    def set_base_prices(self, prices: dict[str, float]) -> None:
        """Set base prices for goods (called by scenario)."""
        self._base_prices = dict(prices)

    def _subscribe_topics(self) -> None:
        pass  # Oracle doesn't subscribe to order topics

    def _handle_message(self, topic: str, envelope: MessageEnvelope) -> None:
        pass  # Oracle is mostly a publisher

    def _on_start(self) -> None:
        self._price_thread = threading.Thread(
            target=self._price_loop, daemon=True, name=f"{self.agent_id}-prices"
        )
        self._price_thread.start()

    def _price_loop(self) -> None:
        """Periodically publish price updates."""
        time.sleep(2)  # Wait for peers to connect
        while self._running:
            try:
                self._publish_prices()
                self._publish_demand()
                self._epoch += 1
            except Exception:
                logger.exception("[%s] Price update error", self.agent_id)
            time.sleep(self.config.epoch_duration / 4)  # 4x per epoch

    def _publish_prices(self) -> None:
        prices = {}
        for goods, base_price in self._base_prices.items():
            # Add some volatility
            volatility = 0.10
            trend = random.uniform(-volatility, volatility)
            current_price = base_price * (1 + trend)
            prices[goods] = {
                "price": round(current_price, 2),
                "trend": round(trend, 4),
                "volatility": volatility,
            }

        update = MarketPriceUpdate(
            oracle_id=self.agent_id,
            prices=prices,
            epoch=self._epoch,
        )
        self.publish(MARKET_PRICES, update, retain=True)
        logger.info("[%s] Published prices epoch=%d: %s", self.agent_id, self._epoch, prices)

    def _publish_demand(self) -> None:
        forecasts = {}
        for goods in self._base_prices:
            forecasts[goods] = {
                "demand": round(random.uniform(20, 100), 0),
                "growth_rate": round(random.uniform(-0.1, 0.2), 3),
            }

        demand = MarketDemand(
            oracle_id=self.agent_id,
            forecasts=forecasts,
            epoch=self._epoch,
        )
        self.publish(MARKET_DEMAND, demand, retain=True)
