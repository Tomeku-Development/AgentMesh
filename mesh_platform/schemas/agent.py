"""Pydantic schemas for agent endpoints."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class AgentDefinitionResponse(BaseModel):
    id: str
    workspace_id: str
    agent_role: str
    agent_mesh_id: str
    capabilities: str
    initial_balance: float
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    agents: list[AgentDefinitionResponse]


class AgentStatusResponse(BaseModel):
    status: str
    load: float
    active_orders: int
    recorded_at: datetime
    model_config = {"from_attributes": True}
