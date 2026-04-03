"""Workspace provisioning service."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.config import settings
from mesh_platform.models.workspace import Workspace, WorkspaceMembership, WorkspaceRole


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:64]


async def create_workspace(
    db: AsyncSession, *, name: str, owner_id: uuid.UUID, slug: str | None = None
) -> Workspace:
    ws = Workspace(
        name=name,
        slug=slug or slugify(name),
        owner_id=owner_id,
        plan=settings.default_plan,
        max_agents=settings.default_max_agents,
    )
    db.add(ws)
    await db.flush()

    membership = WorkspaceMembership(
        workspace_id=ws.id,
        user_id=owner_id,
        role=WorkspaceRole.owner,
    )
    db.add(membership)
    await db.flush()
    return ws


async def list_workspaces_for_user(
    db: AsyncSession, user_id: uuid.UUID
) -> list[Workspace]:
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMembership)
        .where(WorkspaceMembership.user_id == user_id)
    )
    return list(result.scalars().all())


async def get_workspace_by_id(
    db: AsyncSession, workspace_id: uuid.UUID
) -> Workspace | None:
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()


async def check_membership(
    db: AsyncSession, workspace_id: str, user_id: str
) -> WorkspaceMembership | None:
    result = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()
