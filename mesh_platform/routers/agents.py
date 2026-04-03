"""Agent read endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from mesh_platform.dependencies import DBSession, get_workspace
from mesh_platform.models.agent import AgentDefinition, AgentStatusLog
from mesh_platform.models.workspace import Workspace
from mesh_platform.schemas.agent import AgentDefinitionResponse, AgentListResponse, AgentStatusResponse

router = APIRouter(tags=["agents"])


@router.get(
    "/workspaces/{workspace_id}/agents",
    response_model=AgentListResponse,
)
async def list_agents(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: DBSession,
):
    result = await db.execute(
        select(AgentDefinition).where(AgentDefinition.workspace_id == workspace.id)
    )
    return AgentListResponse(agents=list(result.scalars().all()))


@router.get(
    "/workspaces/{workspace_id}/agents/{agent_id}/status",
    response_model=list[AgentStatusResponse],
)
async def get_agent_status(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    agent_id: str,
    db: DBSession,
):
    result = await db.execute(
        select(AgentStatusLog)
        .where(
            AgentStatusLog.agent_definition_id == agent_id,
            AgentStatusLog.workspace_id == workspace.id,
        )
        .order_by(AgentStatusLog.recorded_at.desc())
        .limit(50)
    )
    return list(result.scalars().all())
