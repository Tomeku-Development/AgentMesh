"""LLM usage tracking and quota management service."""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.models.usage import LLMUsageEvent, SubscriptionPlan
from mesh_platform.models.workspace import Workspace

logger = logging.getLogger(__name__)


async def record_llm_usage(
    db: AsyncSession,
    workspace_id: str,
    *,
    user_id: str | None = None,
    agent_id: str | None = None,
    agent_role: str | None = None,
    model: str = "",
    provider: str = "",
    prompt_type: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_estimate: float = 0.0,
    latency_ms: float = 0.0,
) -> LLMUsageEvent:
    """Record an LLM usage event and deduct credits from workspace."""
    # Calculate credits to charge (1 credit per $0.001 of cost)
    credits_charged = cost_estimate * 1000  # Convert USD to credits
    
    event = LLMUsageEvent(
        workspace_id=workspace_id,
        user_id=user_id,
        agent_id=agent_id,
        agent_role=agent_role,
        model=model,
        provider=provider,
        prompt_type=prompt_type,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_estimate=cost_estimate,
        credits_charged=credits_charged,
        latency_ms=latency_ms,
    )
    db.add(event)
    
    # Deduct credits from workspace
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = result.scalar_one_or_none()
    if workspace:
        workspace.credits_used_this_month = (workspace.credits_used_this_month or 0) + credits_charged
        workspace.credits_balance = max(0, (workspace.credits_balance or 0) - credits_charged)
    
    await db.flush()
    logger.info(
        "LLM usage recorded: workspace=%s agent=%s model=%s tokens=%d+%d cost=$%.4f credits=%.1f",
        workspace_id, agent_id, model, input_tokens, output_tokens, cost_estimate, credits_charged,
    )
    return event


async def check_quota(db: AsyncSession, workspace_id: str) -> dict[str, Any]:
    """Check workspace usage quota status."""
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = result.scalar_one_or_none()
    if not workspace:
        return {"allowed": False, "reason": "Workspace not found"}
    
    # Get plan limits
    plan_result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.name == (workspace.plan or "starter"))
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        return {"allowed": True, "reason": "No plan found, allowing by default"}
    
    credits_used = workspace.credits_used_this_month or 0
    credits_limit = plan.monthly_credits
    credits_remaining = max(0, credits_limit - credits_used)
    
    # Check daily request count
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    daily_count_result = await db.execute(
        select(func.count(LLMUsageEvent.id)).where(
            and_(
                LLMUsageEvent.workspace_id == workspace_id,
                LLMUsageEvent.created_at >= today_start,
            )
        )
    )
    daily_requests = daily_count_result.scalar() or 0
    
    exceeded = credits_remaining <= 0 or daily_requests >= plan.llm_requests_per_day
    
    return {
        "allowed": not exceeded,
        "credits_used": credits_used,
        "credits_limit": credits_limit,
        "credits_remaining": credits_remaining,
        "daily_requests": daily_requests,
        "daily_limit": plan.llm_requests_per_day,
        "plan": plan.name,
        "reason": "Quota exceeded" if exceeded else "OK",
    }


async def get_usage_summary(
    db: AsyncSession,
    workspace_id: str,
    days: int = 30,
) -> dict[str, Any]:
    """Get aggregated usage summary for a workspace."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Total aggregates
    totals = await db.execute(
        select(
            func.count(LLMUsageEvent.id).label("total_calls"),
            func.coalesce(func.sum(LLMUsageEvent.input_tokens), 0).label("total_input_tokens"),
            func.coalesce(func.sum(LLMUsageEvent.output_tokens), 0).label("total_output_tokens"),
            func.coalesce(func.sum(LLMUsageEvent.cost_estimate), 0).label("total_cost"),
            func.coalesce(func.sum(LLMUsageEvent.credits_charged), 0).label("total_credits"),
        ).where(
            and_(LLMUsageEvent.workspace_id == workspace_id, LLMUsageEvent.created_at >= since)
        )
    )
    row = totals.one()
    
    # Daily breakdown
    daily_result = await db.execute(
        select(
            func.date(LLMUsageEvent.created_at).label("date"),
            func.count(LLMUsageEvent.id).label("calls"),
            func.coalesce(func.sum(LLMUsageEvent.input_tokens + LLMUsageEvent.output_tokens), 0).label("tokens"),
            func.coalesce(func.sum(LLMUsageEvent.cost_estimate), 0).label("cost"),
        ).where(
            and_(LLMUsageEvent.workspace_id == workspace_id, LLMUsageEvent.created_at >= since)
        ).group_by(func.date(LLMUsageEvent.created_at)).order_by(func.date(LLMUsageEvent.created_at))
    )
    daily = [{"date": str(r.date), "calls": r.calls, "tokens": r.tokens, "cost": float(r.cost)} for r in daily_result.all()]
    
    # By model
    model_result = await db.execute(
        select(
            LLMUsageEvent.model,
            func.count(LLMUsageEvent.id).label("calls"),
            func.coalesce(func.sum(LLMUsageEvent.input_tokens + LLMUsageEvent.output_tokens), 0).label("tokens"),
            func.coalesce(func.sum(LLMUsageEvent.cost_estimate), 0).label("cost"),
        ).where(
            and_(LLMUsageEvent.workspace_id == workspace_id, LLMUsageEvent.created_at >= since)
        ).group_by(LLMUsageEvent.model)
    )
    by_model = [{"model": r.model, "calls": r.calls, "tokens": r.tokens, "cost": float(r.cost)} for r in model_result.all()]
    
    # By agent role
    role_result = await db.execute(
        select(
            LLMUsageEvent.agent_role,
            func.count(LLMUsageEvent.id).label("calls"),
            func.coalesce(func.sum(LLMUsageEvent.input_tokens + LLMUsageEvent.output_tokens), 0).label("tokens"),
            func.coalesce(func.sum(LLMUsageEvent.cost_estimate), 0).label("cost"),
        ).where(
            and_(LLMUsageEvent.workspace_id == workspace_id, LLMUsageEvent.created_at >= since)
        ).group_by(LLMUsageEvent.agent_role)
    )
    by_role = [{"role": r.agent_role or "unknown", "calls": r.calls, "tokens": r.tokens, "cost": float(r.cost)} for r in role_result.all()]
    
    # By prompt type
    type_result = await db.execute(
        select(
            LLMUsageEvent.prompt_type,
            func.count(LLMUsageEvent.id).label("calls"),
            func.coalesce(func.sum(LLMUsageEvent.cost_estimate), 0).label("cost"),
        ).where(
            and_(LLMUsageEvent.workspace_id == workspace_id, LLMUsageEvent.created_at >= since)
        ).group_by(LLMUsageEvent.prompt_type)
    )
    by_type = [{"type": r.prompt_type or "unknown", "calls": r.calls, "cost": float(r.cost)} for r in type_result.all()]
    
    # Get workspace credits info
    ws_result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = ws_result.scalar_one_or_none()
    credits_remaining = (workspace.credits_balance or 0) if workspace else 0
    
    plan_result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.name == (workspace.plan if workspace else "starter"))
    )
    plan = plan_result.scalar_one_or_none()
    credits_limit = plan.monthly_credits if plan else 1000
    
    return {
        "total_calls": row.total_calls,
        "total_input_tokens": row.total_input_tokens,
        "total_output_tokens": row.total_output_tokens,
        "total_cost": float(row.total_cost),
        "total_credits_used": float(row.total_credits),
        "credits_remaining": credits_remaining,
        "credits_limit": credits_limit,
        "period_start": since.isoformat(),
        "period_end": datetime.now(timezone.utc).isoformat(),
        "daily_breakdown": daily,
        "by_model": by_model,
        "by_agent_role": by_role,
        "by_prompt_type": by_type,
    }


async def get_platform_analytics(db: AsyncSession) -> dict[str, Any]:
    """Get platform-wide analytics for admin dashboard."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Count workspaces
    ws_count = await db.execute(select(func.count(Workspace.id)))
    total_workspaces = ws_count.scalar() or 0
    
    # Today's LLM usage
    today_usage = await db.execute(
        select(
            func.count(LLMUsageEvent.id).label("calls"),
            func.coalesce(func.sum(LLMUsageEvent.cost_estimate), 0).label("cost"),
            func.coalesce(func.sum(LLMUsageEvent.input_tokens + LLMUsageEvent.output_tokens), 0).label("tokens"),
        ).where(LLMUsageEvent.created_at >= today_start)
    )
    today = today_usage.one()
    
    # This month's total
    month_usage = await db.execute(
        select(
            func.count(LLMUsageEvent.id).label("calls"),
            func.coalesce(func.sum(LLMUsageEvent.cost_estimate), 0).label("cost"),
        ).where(LLMUsageEvent.created_at >= month_start)
    )
    month = month_usage.one()
    
    # Top workspaces by usage this month
    top_ws = await db.execute(
        select(
            LLMUsageEvent.workspace_id,
            func.count(LLMUsageEvent.id).label("calls"),
            func.coalesce(func.sum(LLMUsageEvent.cost_estimate), 0).label("cost"),
        ).where(LLMUsageEvent.created_at >= month_start)
        .group_by(LLMUsageEvent.workspace_id)
        .order_by(func.sum(LLMUsageEvent.cost_estimate).desc())
        .limit(10)
    )
    top_workspaces = [{"workspace_id": r.workspace_id, "calls": r.calls, "cost": float(r.cost)} for r in top_ws.all()]
    
    # Plan distribution
    plan_dist = await db.execute(
        select(Workspace.plan, func.count(Workspace.id).label("count"))
        .group_by(Workspace.plan)
    )
    plan_distribution = [{"plan": r.plan or "starter", "count": r.count} for r in plan_dist.all()]
    
    # Hourly breakdown for today
    hourly = await db.execute(
        select(
            func.extract("hour", LLMUsageEvent.created_at).label("hour"),
            func.count(LLMUsageEvent.id).label("calls"),
        ).where(LLMUsageEvent.created_at >= today_start)
        .group_by(func.extract("hour", LLMUsageEvent.created_at))
        .order_by(func.extract("hour", LLMUsageEvent.created_at))
    )
    hourly_breakdown = [{"hour": int(r.hour), "calls": r.calls} for r in hourly.all()]
    
    return {
        "total_workspaces": total_workspaces,
        "today": {
            "llm_calls": today.calls,
            "cost": float(today.cost),
            "tokens": today.tokens,
        },
        "this_month": {
            "llm_calls": month.calls,
            "cost": float(month.cost),
        },
        "top_workspaces": top_workspaces,
        "plan_distribution": plan_distribution,
        "hourly_breakdown": hourly_breakdown,
    }
