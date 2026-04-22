"""SLA monitoring router — rule CRUD, evaluation trigger, alert listing, and acknowledgment."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from mesh_platform.dependencies import CurrentUser, DBSession, require_workspace_admin
from mesh_platform.models.workspace import WorkspaceMembership
from mesh_platform.schemas.sla import (
    AlertListResponse,
    EvaluationResponse,
    SLAAlertResponse,
    SLARuleCreate,
    SLARuleListResponse,
    SLARuleResponse,
)
from mesh_platform.services.sla_service import (
    acknowledge_alert,
    create_rule,
    delete_rule,
    evaluate_rules,
    list_alerts,
    list_rules,
)

router = APIRouter(tags=["sla"])


@router.post(
    "/workspaces/{workspace_id}/sla/rules",
    response_model=SLARuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sla_rule(
    body: SLARuleCreate,
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
):
    """Create a new SLA rule for the workspace (admin+ access)."""
    rule = await create_rule(db, membership.workspace_id, body)
    return rule


@router.get(
    "/workspaces/{workspace_id}/sla/rules",
    response_model=SLARuleListResponse,
)
async def list_sla_rules(
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
):
    """List all SLA rules for the workspace (admin+ access)."""
    rules = await list_rules(db, membership.workspace_id)
    return SLARuleListResponse(rules=rules)


@router.delete(
    "/workspaces/{workspace_id}/sla/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_sla_rule(
    rule_id: Annotated[str, Path()],
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
):
    """Delete an SLA rule (admin+ access)."""
    deleted = await delete_rule(db, rule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SLA rule not found"
        )


@router.post(
    "/workspaces/{workspace_id}/sla/evaluate",
    response_model=EvaluationResponse,
)
async def trigger_evaluation(
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
):
    """Trigger SLA evaluation for the workspace (admin+ access)."""
    alerts = await evaluate_rules(db, membership.workspace_id)
    return EvaluationResponse(
        alerts_created=len(alerts),
        alerts=[SLAAlertResponse.model_validate(a) for a in alerts],
    )


@router.get(
    "/workspaces/{workspace_id}/sla/alerts",
    response_model=AlertListResponse,
)
async def list_sla_alerts(
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
):
    """List active (unacknowledged) alerts for the workspace (admin+ access)."""
    alerts = await list_alerts(db, membership.workspace_id)
    return AlertListResponse(alerts=alerts)


@router.post(
    "/workspaces/{workspace_id}/sla/alerts/{alert_id}/acknowledge",
    response_model=SLAAlertResponse,
)
async def acknowledge_sla_alert(
    alert_id: Annotated[str, Path()],
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    user: CurrentUser,
    db: DBSession,
):
    """Acknowledge an SLA alert (admin+ access)."""
    alert = await acknowledge_alert(db, alert_id, user.id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found"
        )
    return alert
