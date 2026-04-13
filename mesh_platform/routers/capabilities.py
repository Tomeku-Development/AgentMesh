"""Capability registry endpoints."""
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from mesh_platform.dependencies import CurrentUser, DBSession, get_workspace
from mesh_platform.models.capability import Capability
from mesh_platform.models.workspace import Workspace
from mesh_platform.schemas.capability import (
    CapabilityListResponse, CapabilityResponse, CreateCapabilityRequest
)

router = APIRouter(tags=["capabilities"])


@router.get("/capabilities", response_model=CapabilityListResponse)
async def list_all_capabilities(db: DBSession):
    """List all system capabilities."""
    result = await db.execute(
        select(Capability).where(Capability.is_system == True).order_by(Capability.category, Capability.name)
    )
    caps = result.scalars().all()
    return CapabilityListResponse(capabilities=caps)


@router.get("/workspaces/{workspace_id}/capabilities", response_model=CapabilityListResponse)
async def list_workspace_capabilities(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: DBSession,
):
    """List system + workspace-specific capabilities."""
    result = await db.execute(
        select(Capability).where(
            (Capability.is_system == True) | (Capability.workspace_id == workspace.id)
        ).order_by(Capability.category, Capability.name)
    )
    caps = result.scalars().all()
    return CapabilityListResponse(capabilities=caps)


@router.post("/workspaces/{workspace_id}/capabilities", response_model=CapabilityResponse, status_code=201)
async def create_capability(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    body: CreateCapabilityRequest,
    user: CurrentUser,
    db: DBSession,
):
    """Create a custom workspace capability."""
    # Normalize name
    normalized = body.name.lower().strip().replace(" ", "_")
    # Check duplicates
    existing = await db.execute(
        select(Capability).where(
            Capability.name == normalized,
            (Capability.is_system == True) | (Capability.workspace_id == workspace.id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Capability '{normalized}' already exists")
    
    cap = Capability(
        name=normalized,
        display_name=body.display_name or body.name.title(),
        category=body.category,
        description=body.description,
        applicable_roles=",".join(body.applicable_roles) if body.applicable_roles else "",
        is_system=False,
        workspace_id=workspace.id,
    )
    db.add(cap)
    await db.flush()
    return cap


@router.delete("/workspaces/{workspace_id}/capabilities/{cap_id}", status_code=204)
async def delete_capability(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    cap_id: str,
    db: DBSession,
):
    """Delete a custom capability (not system ones)."""
    result = await db.execute(
        select(Capability).where(
            Capability.id == cap_id,
            Capability.workspace_id == workspace.id,
            Capability.is_system == False,
        )
    )
    cap = result.scalar_one_or_none()
    if not cap:
        raise HTTPException(status_code=404, detail="Capability not found or cannot be deleted")
    await db.delete(cap)
