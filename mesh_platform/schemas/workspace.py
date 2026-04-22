"""Pydantic request/response schemas for workspaces."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

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


class RoleEnum(str, Enum):
    owner = "owner"
    admin = "admin"
    operator = "operator"
    developer = "developer"
    auditor = "auditor"
    viewer = "viewer"


class RoleUpdateRequest(BaseModel):
    role: RoleEnum


class MembershipResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    role: str

    model_config = {"from_attributes": True}
