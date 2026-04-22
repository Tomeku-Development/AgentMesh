"""SLA monitoring service — rule CRUD, metric computation, evaluation, and alert management."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.models.agent import AgentStatusLog
from mesh_platform.models.order import Order, OrderEvent
from mesh_platform.models.sla import SLAAlert, SLARule
from mesh_platform.schemas.sla import SLARuleCreate


# ---------------------------------------------------------------------------
# Rule CRUD (Requirements 4.1)
# ---------------------------------------------------------------------------


async def create_rule(
    db: AsyncSession,
    workspace_id: str,
    data: SLARuleCreate,
) -> SLARule:
    """Create a new SLA rule for a workspace."""
    rule = SLARule(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        metric_type=data.metric_type.value,
        threshold=data.threshold,
        operator=data.operator.value,
        check_interval_seconds=data.check_interval_seconds,
        is_active=True,
    )
    db.add(rule)
    await db.flush()
    return rule


async def list_rules(
    db: AsyncSession,
    workspace_id: str,
) -> list[SLARule]:
    """List all SLA rules for a workspace."""
    result = await db.execute(
        select(SLARule)
        .where(SLARule.workspace_id == workspace_id)
        .order_by(SLARule.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_rule(
    db: AsyncSession,
    rule_id: str,
) -> bool:
    """Delete an SLA rule. Returns True if deleted, False if not found."""
    result = await db.execute(select(SLARule).where(SLARule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        return False
    await db.delete(rule)
    await db.flush()
    return True


# ---------------------------------------------------------------------------
# Metric computation (Requirements 4.2, 4.6)
# ---------------------------------------------------------------------------


async def compute_order_settlement_time(
    db: AsyncSession,
    workspace_id: str,
    interval_seconds: int,
) -> float:
    """Average seconds from first 'request' OrderEvent to 'settled' OrderEvent per order.

    Returns 0.0 when no settled orders exist in the interval (division-by-zero safe).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=interval_seconds)

    # Subquery: first "request" event per order within the interval
    request_sq = (
        select(
            OrderEvent.order_id,
            func.min(OrderEvent.occurred_at).label("request_at"),
        )
        .where(
            OrderEvent.workspace_id == workspace_id,
            OrderEvent.event_type == "request",
            OrderEvent.occurred_at >= cutoff,
        )
        .group_by(OrderEvent.order_id)
        .subquery()
    )

    # Subquery: last "settled" event per order within the interval
    settled_sq = (
        select(
            OrderEvent.order_id,
            func.max(OrderEvent.occurred_at).label("settled_at"),
        )
        .where(
            OrderEvent.workspace_id == workspace_id,
            OrderEvent.event_type == "settled",
            OrderEvent.occurred_at >= cutoff,
        )
        .group_by(OrderEvent.order_id)
        .subquery()
    )

    # Join and compute average duration using julianday (SQLite compatible)
    avg_q = (
        select(
            func.avg(
                func.julianday(settled_sq.c.settled_at)
                - func.julianday(request_sq.c.request_at)
            ).label("avg_days"),
        )
        .select_from(request_sq)
        .join(settled_sq, request_sq.c.order_id == settled_sq.c.order_id)
    )

    row = (await db.execute(avg_q)).one()
    avg_days = row.avg_days
    if avg_days is None:
        return 0.0
    return float(avg_days) * 86400  # convert days → seconds


async def compute_agent_uptime(
    db: AsyncSession,
    workspace_id: str,
    interval_seconds: int,
) -> float:
    """Percentage of AgentStatusLog records where status is 'active' within the interval.

    Returns 0.0 when no status log records exist (division-by-zero safe).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=interval_seconds)

    result = await db.execute(
        select(
            func.count().label("total"),
            func.count(
                func.nullif(AgentStatusLog.status != "active", True)
            ).label("active_count"),
        ).where(
            AgentStatusLog.workspace_id == workspace_id,
            AgentStatusLog.recorded_at >= cutoff,
        )
    )
    row = result.one()
    total = int(row.total)
    if total == 0:
        return 0.0
    active_count = int(row.active_count)
    return (active_count / total) * 100.0


async def compute_order_success_rate(
    db: AsyncSession,
    workspace_id: str,
    interval_seconds: int,
) -> float:
    """Percentage of orders that reached 'settled' status out of all orders created in the interval.

    Returns 0.0 when no orders exist (division-by-zero safe).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=interval_seconds)

    # Total orders created in the interval
    total_q = select(func.count()).where(
        Order.workspace_id == workspace_id,
        Order.created_at >= cutoff,
    )
    total = (await db.execute(total_q)).scalar() or 0

    if total == 0:
        return 0.0

    # Orders that have a "settled" event in the interval
    settled_q = (
        select(func.count(distinct(OrderEvent.order_id))).where(
            OrderEvent.workspace_id == workspace_id,
            OrderEvent.event_type == "settled",
            OrderEvent.occurred_at >= cutoff,
        )
    )
    settled = (await db.execute(settled_q)).scalar() or 0

    return (settled / total) * 100.0


# Metric dispatcher
_METRIC_COMPUTERS = {
    "order_settlement_time": compute_order_settlement_time,
    "agent_uptime": compute_agent_uptime,
    "order_success_rate": compute_order_success_rate,
}


async def compute_metric(
    db: AsyncSession,
    workspace_id: str,
    metric_type: str,
    interval_seconds: int,
) -> float:
    """Compute the current value for a given metric type."""
    computer = _METRIC_COMPUTERS.get(metric_type)
    if computer is None:
        return 0.0
    return await computer(db, workspace_id, interval_seconds)


# ---------------------------------------------------------------------------
# Evaluation logic (Requirement 4.2)
# ---------------------------------------------------------------------------


async def evaluate_rules(
    db: AsyncSession,
    workspace_id: str,
) -> list[SLAAlert]:
    """Evaluate all active SLA rules for a workspace and create alerts on breach.

    For each active rule, computes the current metric value, compares it against
    the threshold using the rule's operator, and creates an SLAAlert if breached.
    """
    result = await db.execute(
        select(SLARule).where(
            SLARule.workspace_id == workspace_id,
            SLARule.is_active.is_(True),
        )
    )
    rules = result.scalars().all()

    alerts: list[SLAAlert] = []
    for rule in rules:
        actual_value = await compute_metric(
            db, workspace_id, rule.metric_type, rule.check_interval_seconds
        )

        breached = False
        if rule.operator == "greater_than" and actual_value > rule.threshold:
            breached = True
        elif rule.operator == "less_than" and actual_value < rule.threshold:
            breached = True

        if breached:
            alert = SLAAlert(
                id=str(uuid.uuid4()),
                workspace_id=workspace_id,
                rule_id=rule.id,
                metric_type=rule.metric_type,
                actual_value=actual_value,
                threshold_value=rule.threshold,
                breached_at=datetime.now(timezone.utc),
                acknowledged=False,
            )
            db.add(alert)
            alerts.append(alert)

    await db.flush()
    return alerts


# ---------------------------------------------------------------------------
# Alert management (Requirements 4.4, 4.5)
# ---------------------------------------------------------------------------


async def list_alerts(
    db: AsyncSession,
    workspace_id: str,
    unacknowledged_only: bool = True,
) -> list[SLAAlert]:
    """List alerts for a workspace, ordered by breached_at DESC.

    By default returns only unacknowledged alerts (Requirement 4.4).
    """
    query = select(SLAAlert).where(SLAAlert.workspace_id == workspace_id)
    if unacknowledged_only:
        query = query.where(SLAAlert.acknowledged.is_(False))
    query = query.order_by(SLAAlert.breached_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def acknowledge_alert(
    db: AsyncSession,
    alert_id: str,
    user_id: str,
) -> SLAAlert | None:
    """Acknowledge an SLA alert. Returns the updated alert or None if not found.

    Sets acknowledged=True, acknowledged_by, and acknowledged_at (Requirement 4.5).
    """
    result = await db.execute(select(SLAAlert).where(SLAAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        return None
    alert.acknowledged = True
    alert.acknowledged_by = user_id
    alert.acknowledged_at = datetime.now(timezone.utc)
    await db.flush()
    return alert
