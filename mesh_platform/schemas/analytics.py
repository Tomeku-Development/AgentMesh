"""Pydantic schemas for analytics endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Agent Performance Metrics (Requirement 1.1) ──


class AgentMetric(BaseModel):
    agent_id: str
    total_orders: int
    success_rate: float = Field(description="Percentage of settled orders")
    avg_settlement_time_seconds: float
    current_reputation_score: float


class AgentMetricsResponse(BaseModel):
    metrics: list[AgentMetric]


# ── Order Timeline (Requirement 1.2) ──


class OrderPhase(BaseModel):
    model_config = {"populate_by_name": True}

    from_phase: str = Field(alias="from")
    to: str
    duration_seconds: float


class OrderTimeline(BaseModel):
    order_id: str
    phases: list[OrderPhase]


class OrderTimelineResponse(BaseModel):
    timelines: list[OrderTimeline]


# ── Economic Health (Requirement 1.3) ──


class EconomicHealthResponse(BaseModel):
    total_volume: float
    avg_transaction_size: float
    transaction_count: int
    tx_type_counts: dict[str, int]
    escrow_utilization: float
    burn_amount: float
