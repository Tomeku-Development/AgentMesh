"""Pydantic schemas for order endpoints."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class OrderEventResponse(BaseModel):
    id: int
    event_type: str
    agent_id: str
    payload_json: str | None = None
    occurred_at: datetime
    recorded_at: datetime
    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: str
    workspace_id: str
    goods: str
    quantity: int
    max_price_per_unit: float
    current_status: str
    winner_supplier_id: str | None = None
    agreed_price_per_unit: float | None = None
    bid_count: int
    created_at: datetime
    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int
