"""Admin analytics and management endpoints."""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from mesh_platform.dependencies import CurrentUser, DBSession, require_workspace_admin
from mesh_platform.models.usage import LLMUsageEvent, SubscriptionPlan
from mesh_platform.models.workspace import Workspace, WorkspaceMembership
from mesh_platform.models.payment import PaymentIntent
from mesh_platform.schemas.usage import PlanListResponse
from mesh_platform.services.usage_service import (
    get_usage_summary, get_platform_analytics, check_quota,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/analytics")
async def platform_analytics(user: CurrentUser, db: DBSession):
    """Platform-wide analytics (any authenticated user — workspace-level checks done per-endpoint)."""
    data = await get_platform_analytics(db)
    return data


@router.get("/plans", response_model=PlanListResponse)
async def list_plans(db: DBSession):
    """List all available subscription plans."""
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active.is_(True)).order_by(SubscriptionPlan.sort_order)
    )
    plans = result.scalars().all()
    return PlanListResponse(plans=plans)


@router.get("/workspaces/{workspace_id}/usage")
async def workspace_usage(
    workspace_id: str,
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
    days: int = Query(default=30, ge=1, le=365),
):
    """Get workspace usage breakdown (admin+ only)."""
    summary = await get_usage_summary(db, workspace_id, days=days)
    return summary


@router.get("/workspaces/{workspace_id}/quota")
async def workspace_quota(
    workspace_id: str,
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
):
    """Check workspace quota status."""
    quota = await check_quota(db, workspace_id)
    return quota


@router.get("/workspaces/{workspace_id}/usage/export")
async def export_usage_csv(
    workspace_id: str,
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
    days: int = Query(default=30, ge=1, le=365),
):
    """Export workspace usage events as CSV."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    result = await db.execute(
        select(LLMUsageEvent).where(
            LLMUsageEvent.workspace_id == workspace_id,
            LLMUsageEvent.created_at >= since,
        ).order_by(LLMUsageEvent.created_at.desc())
    )
    events = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "agent_id", "agent_role", "model", "provider", "prompt_type",
                      "input_tokens", "output_tokens", "cost_usd", "credits_charged", "latency_ms"])
    for e in events:
        writer.writerow([
            e.created_at.isoformat() if e.created_at else "",
            e.agent_id or "", e.agent_role or "", e.model, e.provider,
            e.prompt_type or "", e.input_tokens, e.output_tokens,
            f"{e.cost_estimate:.4f}", f"{e.credits_charged:.1f}", f"{e.latency_ms:.0f}",
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=usage_{workspace_id}_{days}d.csv"},
    )


@router.put("/workspaces/{workspace_id}/plan")
async def change_workspace_plan(
    workspace_id: str,
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
    plan_name: str = Query(...),
):
    """Change workspace subscription plan (admin+ only)."""
    # Verify plan exists
    plan_result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.name == plan_name, SubscriptionPlan.is_active.is_(True))
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_name}' not found")
    
    # Update workspace
    ws_result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = ws_result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    
    workspace.plan = plan_name
    workspace.max_agents = plan.max_agents
    # Reset credits for new plan
    workspace.credits_balance = plan.monthly_credits
    workspace.credits_used_this_month = 0
    
    await db.flush()
    return {"message": f"Plan changed to {plan.display_name}", "plan": plan_name, "credits": plan.monthly_credits}


@router.get("/workspaces/{workspace_id}/billing")
async def workspace_billing_history(
    workspace_id: str,
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_admin)],
    db: DBSession,
):
    """Get billing history for workspace."""
    result = await db.execute(
        select(PaymentIntent).where(
            PaymentIntent.workspace_id == workspace_id
        ).order_by(PaymentIntent.created_at.desc()).limit(50)
    )
    payments = result.scalars().all()
    
    entries = []
    for p in payments:
        entries.append({
            "id": p.id,
            "type": "payment",
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "description": f"{p.provider} payment",
            "created_at": p.created_at.isoformat() if p.created_at else "",
        })
    
    return {"entries": entries}
