"""Pydantic request/response schemas for workspaces."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class WorkspaceCreateRequest(BaseModel):
    name: str
    slug: str | None = None


class WorkspaceResponse(BaseModel):
    id: str
    slug: str
    name: str
    owner_id: str
    plan: str
    max_agents: int
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceListResponse(BaseModel):
    workspaces: list[WorkspaceResponse]
