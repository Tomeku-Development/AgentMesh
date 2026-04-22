"""Workspace CRUD router."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from mesh_platform.dependencies import CurrentUser, DBSession, get_workspace, require_workspace_admin
from mesh_platform.models.workspace import ROLE_LEVELS, Workspace, WorkspaceMembership
from mesh_platform.schemas.workspace import (
    MembershipResponse,
    RoleUpdateRequest,
    WorkspaceCreateRequest,
    WorkspaceListResponse,
    WorkspaceResponse,
)
from mesh_platform.services.workspace_service import (
    check_membership,
    create_workspace,
    list_workspaces_for_user,
)

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


@router.put(
    "/{workspace_id}/members/{user_id}/role",
    response_model=MembershipResponse,
)
async def update_member_role(
    user_id: Annotated[str, Path()],
    body: RoleUpdateRequest,
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    user: CurrentUser,
    db: DBSession,
):
    """Assign a role to a workspace member with escalation prevention."""
    target_role = body.role.value
    assigner_role = membership.role
    assigner_level = ROLE_LEVELS.get(assigner_role, 0)
    target_level = ROLE_LEVELS.get(target_role, 0)

    # Prevent self-escalation: reject if user tries to assign themselves a higher role
    if str(user.id) == str(user_id):
        current_level = assigner_level
        if target_level > current_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot escalate own role",
            )

    # Assigner's role level must be strictly greater than the target role level
    if assigner_level <= target_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot assign a role equal to or higher than your own",
        )

    # Look up the target user's membership
    target_membership = await check_membership(db, membership.workspace_id, user_id)
    if target_membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in workspace",
        )

    # Update the membership role
    target_membership.role = target_role
    await db.flush()

    return target_membership
