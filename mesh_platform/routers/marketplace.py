"""Marketplace router — agent template CRUD and instantiation."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from mesh_platform.dependencies import (
    CurrentUser,
    DBSession,
    require_workspace_admin,
)
from mesh_platform.models.workspace import WorkspaceMembership
from mesh_platform.schemas.marketplace import (
    InstantiateRequest,
    TemplateCreate,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdate,
)
from mesh_platform.services.marketplace_service import (
    get_template,
    instantiate_template,
    register_template,
    search_templates,
    update_template,
)

router = APIRouter(tags=["marketplace"])


# ── Global endpoints (any authenticated user) ──


@router.post(
    "/marketplace/templates",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    body: TemplateCreate,
    user: CurrentUser,
    db: DBSession,
):
    """Register a new agent template in the marketplace (Requirement 6.1)."""
    return await register_template(db, author_id=user.id, data=body)


@router.get(
    "/marketplace/templates",
    response_model=TemplateListResponse,
)
async def list_templates(
    user: CurrentUser,
    db: DBSession,
    q: Annotated[str | None, Query(description="Text search on name/description")] = None,
    role: Annotated[str | None, Query(description="Filter by agent role")] = None,
    capability: Annotated[str | None, Query(description="Filter by capability")] = None,
):
    """Search/list marketplace templates (Requirement 6.2)."""
    templates = await search_templates(db, q=q, role=role, capability=capability)
    return TemplateListResponse(templates=templates)


@router.get(
    "/marketplace/templates/{template_id}",
    response_model=TemplateResponse,
)
async def get_template_detail(
    template_id: Annotated[str, Path()],
    user: CurrentUser,
    db: DBSession,
):
    """Get a single template by ID (Requirement 6.3)."""
    template = await get_template(db, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return template


@router.put(
    "/marketplace/templates/{template_id}",
    response_model=TemplateResponse,
)
async def update_template_endpoint(
    template_id: Annotated[str, Path()],
    body: TemplateUpdate,
    user: CurrentUser,
    db: DBSession,
):
    """Update a template (author only, Requirement 6.7)."""
    result = await update_template(db, template_id, author_id=user.id, data=body)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or not the author",
        )
    return result


# ── Workspace-scoped endpoint (admin+ required) ──


@router.post(
    "/workspaces/{workspace_id}/marketplace/instantiate/{template_id}",
    status_code=status.HTTP_201_CREATED,
)
async def instantiate_template_endpoint(
    template_id: Annotated[str, Path()],
    body: InstantiateRequest,
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
):
    """Instantiate a template into a workspace AgentDefinition (Requirement 6.4)."""
    agent_def = await instantiate_template(
        db,
        template_id=template_id,
        workspace_id=membership.workspace_id,
        overrides=body,
    )
    if agent_def is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return {
        "id": agent_def.id,
        "workspace_id": agent_def.workspace_id,
        "agent_role": agent_def.agent_role,
        "agent_mesh_id": agent_def.agent_mesh_id,
        "capabilities": agent_def.capabilities,
        "initial_balance": float(agent_def.initial_balance),
        "is_active": agent_def.is_active,
    }
