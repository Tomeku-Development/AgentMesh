"""Analytics endpoints — agent performance, order timeline, economic health."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from mesh_platform.dependencies import DBSession, require_workspace_admin
from mesh_platform.models.workspace import WorkspaceMembership
from mesh_platform.schemas.analytics import (
    AgentMetricsResponse,
    EconomicHealthResponse,
    OrderTimelineResponse,
)
from mesh_platform.services.analytics_service import (
    get_agent_metrics,
    get_economic_health,
    get_order_timeline,
)

router = APIRouter(tags=["analytics"])


@router.get(
    "/workspaces/{workspace_id}/analytics/agents",
    response_model=AgentMetricsResponse,
)
async def agent_analytics(
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
    days: int = Query(default=30, ge=1, le=365),
):
    metrics = await get_agent_metrics(db, membership.workspace_id, days)
    return AgentMetricsResponse(metrics=metrics)


@router.get(
    "/workspaces/{workspace_id}/analytics/orders/timeline",
    response_model=OrderTimelineResponse,
)
async def order_timeline(
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
    days: int = Query(default=30, ge=1, le=365),
):
    timelines = await get_order_timeline(db, membership.workspace_id, days)
    return OrderTimelineResponse(timelines=timelines)


@router.get(
    "/workspaces/{workspace_id}/analytics/economic",
    response_model=EconomicHealthResponse,
)
async def economic_health(
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
    days: int = Query(default=30, ge=1, le=365),
):
    result = await get_economic_health(db, membership.workspace_id, days)
    return EconomicHealthResponse(**result)
