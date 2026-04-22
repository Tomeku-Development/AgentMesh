"""Pydantic request/response schemas for the agent marketplace."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# ── Request schemas ──


class TemplateCreate(BaseModel):
    """Create a new agent template in the marketplace (Requirement 6.1)."""

    name: str = Field(min_length=3, max_length=100, description="Template name (3-100 chars)")
    description: str | None = Field(default=None, description="Optional description")
    agent_role: str = Field(description="Agent role, e.g. 'buyer', 'supplier'")
    capabilities: list[str] = Field(default_factory=list, description="Capability tags")
    default_initial_balance: float = Field(default=0.0, ge=0, description="Default starting balance")
    config: dict = Field(default_factory=dict, description="Configuration parameters as JSON")


class TemplateUpdate(BaseModel):
    """Update an existing agent template (Requirement 6.7). All fields optional."""

    name: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = None
    agent_role: str | None = None
    capabilities: list[str] | None = None
    default_initial_balance: float | None = Field(default=None, ge=0)
    config: dict | None = None


class InstantiateRequest(BaseModel):
    """Instantiate a template into a workspace with optional overrides (Requirement 6.4)."""

    initial_balance: float | None = Field(default=None, ge=0, description="Override initial balance")
    capabilities: list[str] | None = Field(
        default=None, description="Override capabilities list"
    )


# ── Response schemas ──


class TemplateResponse(BaseModel):
    """Full template detail response (Requirement 6.3)."""

    id: str
    name: str
    description: str | None
    agent_role: str
    capabilities: list[str]
    default_initial_balance: float
    config: dict
    author_id: str
    usage_count: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class TemplateListResponse(BaseModel):
    """List wrapper for template search results (Requirement 6.2)."""

    templates: list[TemplateResponse]
