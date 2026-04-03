"""Workspace CRUD router."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from mesh_platform.dependencies import CurrentUser, DBSession, get_workspace
from mesh_platform.models.workspace import Workspace
from mesh_platform.schemas.workspace import (
    WorkspaceCreateRequest,
    WorkspaceListResponse,
    WorkspaceResponse,
)
from mesh_platform.services.workspace_service import create_workspace, list_workspaces_for_user

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create(body: WorkspaceCreateRequest, user: CurrentUser, db: DBSession):
    from sqlalchemy import select

    if body.slug:
        existing = await db.execute(select(Workspace).where(Workspace.slug == body.slug))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already taken")

    ws = await create_workspace(db, name=body.name, owner_id=user.id, slug=body.slug)
    return ws


@router.get("", response_model=WorkspaceListResponse)
async def list_ws(user: CurrentUser, db: DBSession):
    workspaces = await list_workspaces_for_user(db, user.id)
    return WorkspaceListResponse(workspaces=workspaces)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_ws(workspace: Annotated[Workspace, Depends(get_workspace)]):
    return workspace
