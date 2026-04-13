"""MarketOracleAgent — publishes price feeds and demand forecasts."""

from __future__ import annotations

import asyncio
import logging
import random
import threading
import time

from mesh.agents.base import BaseAgent
from mesh.core.messages import MarketDemand, MarketPriceUpdate, MessageEnvelope
from mesh.core.topics import MARKET_DEMAND, MARKET_PRICES
from mesh.llm.prompts import oracle_demand_prompt, oracle_pricing_prompt
from mesh.llm.router import LLMRouter

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
        self._price_history: dict[str, list[float]] = {}  # goods -> last N prices
        self._llm_router = LLMRouter(config)
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
        """Publish price updates using LLM or fallback to random."""
        try:
            prices = self._llm_publish_prices()
            logger.info(
                "[%s] Published prices (LLM) epoch=%d: %s",
                self.agent_id, self._epoch, prices,
            )
        except Exception as e:
            logger.warning("[%s] LLM pricing failed, using fallback: %s", self.agent_id, e)
            prices = self._fallback_prices()
            logger.info(
                "[%s] Published prices (fallback) epoch=%d: %s",
                self.agent_id, self._epoch, prices,
            )

        update = MarketPriceUpdate(
            oracle_id=self.agent_id,
            prices=prices,
            epoch=self._epoch,
        )
        self.publish(MARKET_PRICES, update, retain=True)

    def _llm_publish_prices(self) -> dict:
        """Use LLM to determine market prices. Raises on failure."""
        agent_count = 0
        if hasattr(self, 'registry') and hasattr(self.registry, 'get_all_peers'):
            agent_count = len(self.registry.get_all_peers())

        # Convert price history to list format for prompt
        history_list = []
        for goods, prices_list in self._price_history.items():
            if prices_list:
                history_list.append({"goods": goods, "recent_prices": prices_list[-10:]})

        system_prompt, user_prompt = oracle_pricing_prompt(
            self._base_prices, history_list, self._epoch, agent_count
        )

        result = asyncio.run(self._llm_router.complete_json(user_prompt, system_prompt))

        # Parse LLM response expecting per-goods pricing
        prices = {}
        llm_prices = result.get("prices", {})

        for goods, base_price in self._base_prices.items():
            if goods in llm_prices:
                goods_data = llm_prices[goods]
                price = float(goods_data.get("price", base_price))
                trend = float(goods_data.get("trend", 0.0))
                volatility = float(goods_data.get("volatility", 0.1))

                # Validate: price must be within 50% of base price
                min_price = base_price * 0.5
                max_price = base_price * 1.5
                price = max(min_price, min(max_price, price))

                # Validate: trend in [-0.5, 0.5]
                trend = max(-0.5, min(0.5, trend))

                # Validate: volatility in [0.01, 0.5]
                volatility = max(0.01, min(0.5, volatility))
            else:
                # Fallback to base if goods not in response
                price, trend, volatility = base_price, 0.0, 0.1

            prices[goods] = {
                "price": round(price, 2),
                "trend": round(trend, 4),
                "volatility": round(volatility, 4),
            }

            # Update price history
            if goods not in self._price_history:
                self._price_history[goods] = []
            self._price_history[goods].append(price)
            # Keep last 10 prices
            if len(self._price_history[goods]) > 10:
                self._price_history[goods] = self._price_history[goods][-10:]

        return prices

    def _fallback_prices(self) -> dict:
        """Fallback to random-based pricing when LLM fails."""
        prices = {}
        for goods, base_price in self._base_prices.items():
            volatility = 0.10
            trend = random.uniform(-volatility, volatility)
            current_price = base_price * (1 + trend)
            prices[goods] = {
                "price": round(current_price, 2),
                "trend": round(trend, 4),
                "volatility": volatility,
            }
            # Update price history for fallback too
            if goods not in self._price_history:
                self._price_history[goods] = []
            self._price_history[goods].append(current_price)
            if len(self._price_history[goods]) > 10:
                self._price_history[goods] = self._price_history[goods][-10:]
        return prices

    def _publish_demand(self) -> None:
        """Publish demand forecasts using LLM or fallback to random."""
        try:
            forecasts = self._llm_publish_demand()
            logger.info("[%s] Published demand (LLM) epoch=%d", self.agent_id, self._epoch)
        except Exception as e:
            logger.warning("[%s] LLM demand failed, using fallback: %s", self.agent_id, e)
            forecasts = self._fallback_demand()
            logger.info("[%s] Published demand (fallback) epoch=%d", self.agent_id, self._epoch)

        demand = MarketDemand(
            oracle_id=self.agent_id,
            forecasts=forecasts,
            epoch=self._epoch,
        )
        self.publish(MARKET_DEMAND, demand, retain=True)

    def _llm_publish_demand(self) -> dict:
        """Use LLM to analyze demand patterns. Raises on failure."""
        # Build goods catalog from base prices
        goods_catalog = [{"name": goods, "base_price": price}
                         for goods, price in self._base_prices.items()]

        system_prompt, user_prompt = oracle_demand_prompt(
            goods_catalog, self._price_history, self._epoch
        )

        result = asyncio.run(self._llm_router.complete_json(user_prompt, system_prompt))

        # Parse LLM response expecting demand_forecast
        forecasts = {}
        demand_forecast = result.get("demand_forecast", {})

        for goods in self._base_prices:
            if goods in demand_forecast:
                goods_data = demand_forecast[goods]
                demand = float(goods_data.get("demand", 50))
                growth_rate = float(goods_data.get("growth_rate", 0.0))

                # Validate: demand in [1, 500]
                demand = max(1, min(500, demand))
                # Validate: growth_rate in [-0.5, 0.5]
                growth_rate = max(-0.5, min(0.5, growth_rate))
            else:
                demand, growth_rate = 50.0, 0.0

            forecasts[goods] = {
                "demand": round(demand, 0),
                "growth_rate": round(growth_rate, 3),
            }

        return forecasts

    def _fallback_demand(self) -> dict:
        """Fallback to random-based demand when LLM fails."""
        forecasts = {}
        for goods in self._base_prices:
            forecasts[goods] = {
                "demand": round(random.uniform(20, 100), 0),
                "growth_rate": round(random.uniform(-0.1, 0.2), 3),
            }
        return forecasts
