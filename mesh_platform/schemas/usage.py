"""Pydantic schemas for usage and billing endpoints."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class UsageEventResponse(BaseModel):
    id: str
    workspace_id: str
    agent_id: str | None = None
    agent_role: str | None = None
    model: str
    provider: str
    prompt_type: str | None = None
    input_tokens: int
    output_tokens: int
    cost_estimate: float
    credits_charged: float
    latency_ms: float
    created_at: datetime
    model_config = {"from_attributes": True}


class UsageSummaryResponse(BaseModel):
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    total_credits_used: float = 0.0
    credits_remaining: float = 0.0
    credits_limit: float = 0.0
    period_start: str = ""
    period_end: str = ""
    daily_breakdown: list[dict] = []  # [{date, calls, tokens, cost}, ...]
    by_model: list[dict] = []  # [{model, calls, tokens, cost}, ...]
    by_agent_role: list[dict] = []  # [{role, calls, tokens, cost}, ...]
    by_prompt_type: list[dict] = []  # [{type, calls, tokens, cost}, ...]


class PlanResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    monthly_price: float
    monthly_credits: int
    max_agents: int
    max_workspaces: int
    max_api_keys: int
    llm_requests_per_day: int
    llm_tokens_per_month: int
    features_json: dict = {}
    sort_order: int = 0
    is_active: bool = True
    model_config = {"from_attributes": True}


class PlanListResponse(BaseModel):
    plans: list[PlanResponse]


class BillingEntryResponse(BaseModel):
    id: str
    type: str  # "payment", "credit_purchase", "usage_charge"
    amount: float
    currency: str = "USD"
    status: str
    description: str = ""
    created_at: datetime
    model_config = {"from_attributes": True}
