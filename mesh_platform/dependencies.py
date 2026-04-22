"""FastAPI dependency injection: DB sessions, current user, workspace access."""

from __future__ import annotations


from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.config import settings
from mesh_platform.models.base import async_session_factory
from mesh_platform.models.user import User
from mesh_platform.models.workspace import WorkspaceMembership, WorkspaceRole
from mesh_platform.services import auth_service


async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    authorization: Annotated[str, Header()],
    db: DBSession,
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth header")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = auth_service.decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = payload["sub"]
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = await auth_service.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_workspace(
    workspace_id: Annotated[str, Path()],
    user: CurrentUser,
    db: DBSession,
):
    from mesh_platform.services.workspace_service import check_membership, get_workspace_by_id

    ws = await get_workspace_by_id(db, workspace_id)
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    membership = await check_membership(db, ws.id, user.id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    return ws


async def require_workspace_admin(
    workspace_id: Annotated[str, Path()],
    user: CurrentUser,
    db: DBSession,
) -> WorkspaceMembership:
    """Require user to be admin or owner of the workspace."""
    from mesh_platform.services.workspace_service import check_membership

    membership = await check_membership(db, workspace_id, user.id)
    if not membership or membership.role not in [WorkspaceRole.owner.value, WorkspaceRole.admin.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return membership


async def require_workspace_operator(
    workspace_id: Annotated[str, Path()],
    user: CurrentUser,
    db: DBSession,
) -> WorkspaceMembership:
    """Require user to be operator, admin, or owner of the workspace."""
    from mesh_platform.services.workspace_service import check_membership

    membership = await check_membership(db, workspace_id, user.id)
    if not membership or membership.role not in [
        WorkspaceRole.owner.value,
        WorkspaceRole.admin.value,
        WorkspaceRole.operator.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Operator access required"
        )
    return membership


async def require_workspace_auditor(
    workspace_id: Annotated[str, Path()],
    user: CurrentUser,
    db: DBSession,
) -> WorkspaceMembership:
    """Require user to be auditor, admin, or owner of the workspace."""
    from mesh_platform.services.workspace_service import check_membership

    membership = await check_membership(db, workspace_id, user.id)
    if not membership or membership.role not in [
        WorkspaceRole.owner.value,
        WorkspaceRole.admin.value,
        WorkspaceRole.auditor.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Auditor access required"
        )
    return membership


async def require_workspace_developer(
    workspace_id: Annotated[str, Path()],
    user: CurrentUser,
    db: DBSession,
) -> WorkspaceMembership:
    """Require user to be developer, admin, or owner of the workspace."""
    from mesh_platform.services.workspace_service import check_membership

    membership = await check_membership(db, workspace_id, user.id)
    if not membership or membership.role not in [
        WorkspaceRole.owner.value,
        WorkspaceRole.admin.value,
        WorkspaceRole.developer.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Developer access required"
        )
    return membership


async def require_workspace_owner(
    workspace_id: Annotated[str, Path()],
    user: CurrentUser,
    db: DBSession,
) -> WorkspaceMembership:
    """Require user to be owner of the workspace."""
    from mesh_platform.services.workspace_service import check_membership

    membership = await check_membership(db, workspace_id, user.id)
    if not membership or membership.role != WorkspaceRole.owner.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    return membership
