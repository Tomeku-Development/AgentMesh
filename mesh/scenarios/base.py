"""Base scenario definition."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GoodsDefinition:
    name: str
    category: str
    base_price: float
    volatility: float = 0.10


@dataclass
class AgentDefinition:
    role: str
    count: int = 1
    initial_balance: float = 5000.0
    capabilities: list[str] = field(default_factory=list)
    inventory: dict[str, int] = field(default_factory=dict)
    costs: dict[str, float] = field(default_factory=dict)


@dataclass
class OrderEvent:
    at_second: float
    goods: str
    category: str
    quantity: int
    max_price_per_unit: float
    quality_threshold: float = 0.85


@dataclass
class ChaosEvent:
    at_second: float
    event_type: str  # "kill_agent", "restart_agent", "partition"
    target: str  # agent role or ID


class BaseScenario(ABC):
    """Base class for demo scenarios."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def duration_seconds(self) -> int: ...

    @property
    @abstractmethod
    def goods(self) -> list[GoodsDefinition]: ...

    @property
    @abstractmethod
    def agents(self) -> list[AgentDefinition]: ...

    @property
    @abstractmethod
    def orders(self) -> list[OrderEvent]: ...

    @property
    def chaos_events(self) -> list[ChaosEvent]:
        return []

    def get_base_prices(self) -> dict[str, float]:
        return {g.name: g.base_price for g in self.goods}
