"""API key management endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from mesh_platform.dependencies import CurrentUser, DBSession, get_workspace
from mesh_platform.models.workspace import Workspace
from mesh_platform.schemas.api_key import (
    APIKeyCreatedResponse,
    APIKeyListResponse,
    CreateAPIKeyRequest,
)
from mesh_platform.services.api_key_service import (
    generate_api_key,
    list_api_keys,
    revoke_api_key,
)

router = APIRouter(tags=["api-keys"])


@router.post(
    "/workspaces/{workspace_id}/api-keys",
    response_model=APIKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    body: CreateAPIKeyRequest,
    user: CurrentUser,
    db: DBSession,
):
    scopes_str = ",".join(body.scopes) if body.scopes else ""
    raw_key, api_key = await generate_api_key(
        db,
        user_id=user.id,
        workspace_id=workspace.id,
        name=body.name,
        scopes=scopes_str,
        expires_in_days=body.expires_in_days,
    )
    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        raw_key=raw_key,
        scopes=api_key.scopes,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
    )


@router.get(
    "/workspaces/{workspace_id}/api-keys",
    response_model=APIKeyListResponse,
)
async def list_keys(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: DBSession,
):
    keys = await list_api_keys(db, workspace.id)
    return APIKeyListResponse(keys=keys)


@router.delete(
    "/workspaces/{workspace_id}/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_key(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    key_id: str,
    db: DBSession,
):
    revoked = await revoke_api_key(db, key_id, workspace.id)
    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")
