"""Electronics supply chain demo scenario — 'Laptop Supply Chain Crisis'."""

from __future__ import annotations

from mesh.scenarios.base import (
    AgentDefinition,
    BaseScenario,
    ChaosEvent,
    GoodsDefinition,
    OrderEvent,
)


class ElectronicsScenario(BaseScenario):
    """Three-minute demo: buy laptop components, negotiate, ship, inspect, self-heal."""

    @property
    def name(self) -> str:
        return "Laptop Supply Chain"

    @property
    def description(self) -> str:
        return (
            "Buyer orders laptop displays, batteries, and keyboards from competing suppliers. "
            "A supplier failure mid-scenario triggers self-healing role redistribution."
        )

    @property
    def duration_seconds(self) -> int:
        return 180

    @property
    def goods(self) -> list[GoodsDefinition]:
        return [
            GoodsDefinition("laptop_display_15inch", "electronics", base_price=110, volatility=0.15),
            GoodsDefinition("laptop_battery_80wh", "electronics", base_price=45, volatility=0.10),
            GoodsDefinition("laptop_keyboard_us", "electronics", base_price=25, volatility=0.05),
        ]

    @property
    def agents(self) -> list[AgentDefinition]:
        return [
            AgentDefinition(
                role="buyer", count=1, initial_balance=10000,
                capabilities=["electronics"],
            ),
            AgentDefinition(
                role="supplier", count=1, initial_balance=5000,
                capabilities=["electronics", "displays", "keyboards"],
                inventory={"laptop_display_15inch": 200, "laptop_keyboard_us": 300},
                costs={"laptop_display_15inch": 85, "laptop_keyboard_us": 18},
            ),
            AgentDefinition(
                role="supplier", count=1, initial_balance=5000,
                capabilities=["electronics", "batteries", "keyboards"],
                inventory={"laptop_battery_80wh": 500, "laptop_keyboard_us": 200},
                costs={"laptop_battery_80wh": 30, "laptop_keyboard_us": 18},
            ),
            AgentDefinition(
                role="logistics", count=1, initial_balance=2000,
                capabilities=["shipping", "fragile"],
            ),
            AgentDefinition(
                role="inspector", count=1, initial_balance=2000,
                capabilities=["quality_control", "electronics"],
            ),
            AgentDefinition(
                role="oracle", count=1, initial_balance=1000,
                capabilities=["market_data"],
            ),
        ]

    @property
    def orders(self) -> list[OrderEvent]:
        return [
            OrderEvent(
                at_second=8,
                goods="laptop_display_15inch",
                category="electronics",
                quantity=50,
                max_price_per_unit=120,
                quality_threshold=0.85,
            ),
            OrderEvent(
                at_second=50,
                goods="laptop_battery_80wh",
                category="electronics",
                quantity=100,
                max_price_per_unit=50,
                quality_threshold=0.80,
            ),
            OrderEvent(
                at_second=100,
                goods="laptop_keyboard_us",
                category="electronics",
                quantity=75,
                max_price_per_unit=30,
                quality_threshold=0.85,
            ),
        ]

    @property
    def chaos_events(self) -> list[ChaosEvent]:
        return [
            ChaosEvent(at_second=70, event_type="kill_agent", target="supplier_1"),
            ChaosEvent(at_second=110, event_type="restart_agent", target="supplier_1"),
        ]
