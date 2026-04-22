"""Pydantic request/response schemas for SLA monitoring and alerts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ── Enums for validation (Requirement 4.1) ──


class MetricType(str, Enum):
    order_settlement_time = "order_settlement_time"
    agent_uptime = "agent_uptime"
    order_success_rate = "order_success_rate"


class Operator(str, Enum):
    less_than = "less_than"
    greater_than = "greater_than"


# ── Request schemas ──


class SLARuleCreate(BaseModel):
    """Create a new SLA rule (Requirement 4.1)."""

    metric_type: MetricType = Field(description="Metric to monitor")
    threshold: float = Field(description="Threshold value for breach detection")
    operator: Operator = Field(description="Comparison operator for threshold check")
    check_interval_seconds: int = Field(
        gt=0, description="Evaluation interval in seconds, must be > 0"
    )


# ── Response schemas ──


class SLARuleResponse(BaseModel):
    """SLA rule detail (Requirement 4.1)."""

    id: str
    workspace_id: str
    metric_type: str
    threshold: float
    operator: str
    check_interval_seconds: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SLARuleListResponse(BaseModel):
    """List wrapper for SLA rules."""

    rules: list[SLARuleResponse]


class SLAAlertResponse(BaseModel):
    """SLA alert detail (Requirement 4.3)."""

    id: str
    workspace_id: str
    rule_id: str
    metric_type: str
    actual_value: float
    threshold_value: float
    breached_at: datetime
    acknowledged: bool
    acknowledged_by: str | None
    acknowledged_at: datetime | None

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    """List wrapper for SLA alerts (Requirement 4.4)."""

    alerts: list[SLAAlertResponse]


class EvaluationResponse(BaseModel):
    """Result of an SLA evaluation run (Requirement 4.2)."""

    alerts_created: int = Field(description="Number of new alerts created during evaluation")
    alerts: list[SLAAlertResponse] = Field(description="List of newly created alerts")
