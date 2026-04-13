"""Pydantic schemas for capability endpoints."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class CapabilityResponse(BaseModel):
    id: str
    name: str
    display_name: str
    category: str
    description: str
    applicable_roles: str
    is_system: bool
    workspace_id: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class CreateCapabilityRequest(BaseModel):
    name: str
    display_name: str
    category: str = "domain"
    description: str = ""
    applicable_roles: list[str] = []


class CapabilityListResponse(BaseModel):
    capabilities: list[CapabilityResponse]
