"""Pydantic request/response schemas for custom scenario builder."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


# ── Nested definition models (Requirement 3.1) ──


class AgentConfig(BaseModel):
    role: str = Field(description="Agent role, e.g. 'buyer' or 'supplier'")
    count: int = Field(ge=1, description="Number of agents with this role")
    initial_balance: float = Field(ge=0, description="Starting MESH_CREDIT balance")
    capabilities: list[str] = Field(default_factory=list, description="Capability tags")


class GoodsDefinition(BaseModel):
    name: str = Field(min_length=1, description="Goods name (non-empty)")
    category: str = Field(min_length=1, description="Goods category (non-empty)")
    base_price: float = Field(gt=0, description="Base price, must be > 0")
    volatility: float | None = Field(default=None, ge=0, le=1, description="Price volatility 0-1")


class OrderConfig(BaseModel):
    at_second: int = Field(ge=0, description="Seconds into scenario to place order")
    goods: str = Field(description="Goods name to order")
    category: str = Field(description="Goods category")
    quantity: int = Field(ge=1, description="Number of units")
    max_price_per_unit: float = Field(gt=0, description="Maximum price per unit")
    quality_threshold: float = Field(
        ge=0, le=1, default=0.8, description="Minimum quality score 0-1"
    )


class ChaosEventConfig(BaseModel):
    at_second: int = Field(ge=0, description="Seconds into scenario to trigger event")
    event_type: str = Field(description="Type of chaos event, e.g. 'kill_agent'")
    target: str = Field(description="Target of the chaos event, e.g. 'supplier'")


# ── Scenario definition (Requirements 3.1, 3.2, 3.7) ──


class ScenarioDefinition(BaseModel):
    agents: list[AgentConfig]
    goods: list[GoodsDefinition]
    orders: list[OrderConfig] = Field(default_factory=list)
    chaos_events: list[ChaosEventConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_scenario_constraints(self) -> ScenarioDefinition:
        # At least one buyer agent (Requirement 3.2)
        buyer_count = sum(1 for a in self.agents if a.role == "buyer")
        if buyer_count < 1:
            raise ValueError("Scenario must contain at least one buyer agent")

        # At least one supplier agent (Requirement 3.2)
        supplier_count = sum(1 for a in self.agents if a.role == "supplier")
        if supplier_count < 1:
            raise ValueError("Scenario must contain at least one supplier agent")

        # At least one goods definition (Requirement 3.2)
        if len(self.goods) < 1:
            raise ValueError("Scenario must contain at least one goods definition")

        return self


# ── Request schemas ──


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200, description="Scenario name (3-200 chars)")
    description: str | None = Field(default=None, description="Optional description")
    duration_seconds: int = Field(gt=0, description="Scenario duration in seconds")
    definition: ScenarioDefinition


class ScenarioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    duration_seconds: int | None = Field(default=None, gt=0)
    definition: ScenarioDefinition | None = None


# ── Response schemas ──


class ScenarioResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: str | None
    duration_seconds: int
    definition: ScenarioDefinition
    is_system: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ScenarioListResponse(BaseModel):
    scenarios: list[ScenarioResponse]
