"""Scenario CRUD router — custom supply chain scenario builder."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from mesh_platform.dependencies import DBSession, get_workspace, require_workspace_owner
from mesh_platform.models.workspace import Workspace, WorkspaceMembership
from mesh_platform.schemas.scenario import (
    ScenarioCreate,
    ScenarioListResponse,
    ScenarioResponse,
    ScenarioUpdate,
)
from mesh_platform.services.scenario_service import (
    create_scenario,
    delete_scenario,
    get_scenario,
    list_scenarios,
    update_scenario,
)

router = APIRouter(tags=["scenarios"])


@router.post(
    "/workspaces/{workspace_id}/scenarios",
    response_model=ScenarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    body: ScenarioCreate,
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_owner)],
    db: DBSession,
):
    """Create a new custom scenario in the workspace (owner only)."""
    return await create_scenario(db, membership.workspace_id, body)


@router.get(
    "/workspaces/{workspace_id}/scenarios",
    response_model=ScenarioListResponse,
)
async def list_all(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: DBSession,
):
    """List all scenarios for the workspace, including built-in system scenarios (viewer+ access)."""
    scenarios = await list_scenarios(db, workspace.id)
    return ScenarioListResponse(scenarios=scenarios)


@router.get(
    "/workspaces/{workspace_id}/scenarios/{scenario_id}",
    response_model=ScenarioResponse,
)
async def get_detail(
    scenario_id: Annotated[str, Path()],
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: DBSession,
):
    """Get a single scenario by ID (viewer+ access)."""
    scenario = await get_scenario(db, scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found"
        )
    return scenario


@router.put(
    "/workspaces/{workspace_id}/scenarios/{scenario_id}",
    response_model=ScenarioResponse,
)
async def update(
    scenario_id: Annotated[str, Path()],
    body: ScenarioUpdate,
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_owner)],
    db: DBSession,
):
    """Update an existing scenario (owner only)."""
    scenario = await update_scenario(db, scenario_id, body)
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found"
        )
    return scenario


@router.delete(
    "/workspaces/{workspace_id}/scenarios/{scenario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete(
    scenario_id: Annotated[str, Path()],
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_owner)],
    db: DBSession,
):
    """Delete a scenario (owner only)."""
    deleted = await delete_scenario(db, scenario_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found"
        )
