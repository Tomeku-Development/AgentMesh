"""Analytics service — aggregation queries over event-sourced tables."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.models.ledger import EscrowRecord, LedgerEntry
from mesh_platform.models.order import OrderEvent
from mesh_platform.models.reputation import ReputationSnapshot


async def get_agent_metrics(
    db: AsyncSession,
    workspace_id: str,
    days: int = 30,
) -> list[dict]:
    """Per-agent performance metrics: total orders, success rate, avg settlement time, reputation.

    Returns an empty list when no data exists.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # ── Per-agent order counts and settled counts ──
    order_stats_q = (
        select(
            OrderEvent.agent_id,
            func.count(distinct(OrderEvent.order_id)).label("total_orders"),
            func.count(
                distinct(
                    case(
                        (OrderEvent.event_type == "settled", OrderEvent.order_id),
                        else_=None,
                    )
                )
            ).label("settled_count"),
        )
        .where(
            OrderEvent.workspace_id == workspace_id,
            OrderEvent.occurred_at >= cutoff,
        )
        .group_by(OrderEvent.agent_id)
    )
    order_rows = (await db.execute(order_stats_q)).all()

    if not order_rows:
        return []

    # ── Average settlement time per agent ──
    # First event ("request") per order
    first_event_sq = (
        select(
            OrderEvent.order_id,
            func.min(OrderEvent.occurred_at).label("first_at"),
        )
        .where(
            OrderEvent.workspace_id == workspace_id,
            OrderEvent.occurred_at >= cutoff,
        )
        .group_by(OrderEvent.order_id)
        .subquery()
    )

    # Last "settled" event per order
    settled_sq = (
        select(
            OrderEvent.order_id,
            OrderEvent.agent_id,
            func.max(OrderEvent.occurred_at).label("settled_at"),
        )
        .where(
            OrderEvent.workspace_id == workspace_id,
            OrderEvent.event_type == "settled",
            OrderEvent.occurred_at >= cutoff,
        )
        .group_by(OrderEvent.order_id, OrderEvent.agent_id)
        .subquery()
    )

    settlement_q = (
        select(
            settled_sq.c.agent_id,
            func.avg(
                func.julianday(settled_sq.c.settled_at)
                - func.julianday(first_event_sq.c.first_at)
            ).label("avg_days"),
        )
        .join(first_event_sq, settled_sq.c.order_id == first_event_sq.c.order_id)
        .group_by(settled_sq.c.agent_id)
    )
    settlement_rows = {
        row.agent_id: (row.avg_days or 0.0) * 86400  # convert days → seconds
        for row in (await db.execute(settlement_q)).all()
    }

    # ── Latest reputation snapshot per agent ──
    latest_rep_sq = (
        select(
            ReputationSnapshot.agent_id,
            func.max(ReputationSnapshot.snapshot_at).label("latest_at"),
        )
        .where(ReputationSnapshot.workspace_id == workspace_id)
        .group_by(ReputationSnapshot.agent_id)
        .subquery()
    )

    rep_q = (
        select(
            ReputationSnapshot.agent_id,
            func.avg(ReputationSnapshot.score).label("avg_score"),
        )
        .join(
            latest_rep_sq,
            (ReputationSnapshot.agent_id == latest_rep_sq.c.agent_id)
            & (ReputationSnapshot.snapshot_at == latest_rep_sq.c.latest_at),
        )
        .where(ReputationSnapshot.workspace_id == workspace_id)
        .group_by(ReputationSnapshot.agent_id)
    )
    rep_map = {
        row.agent_id: float(row.avg_score)
        for row in (await db.execute(rep_q)).all()
    }

    # ── Assemble results ──
    results = []
    for row in order_rows:
        total = int(row.total_orders)
        settled = int(row.settled_count)
        success_rate = (settled / total * 100.0) if total > 0 else 0.0
        results.append(
            {
                "agent_id": row.agent_id,
                "total_orders": total,
                "success_rate": round(success_rate, 2),
                "avg_settlement_time_seconds": round(
                    settlement_rows.get(row.agent_id, 0.0), 2
                ),
                "current_reputation_score": round(
                    rep_map.get(row.agent_id, 0.0), 4
                ),
            }
        )
    return results


async def get_order_timeline(
    db: AsyncSession,
    workspace_id: str,
    days: int = 30,
) -> list[dict]:
    """Order phase transition durations.

    For each order, returns the duration in seconds between consecutive
    OrderEvent phase transitions.  Returns an empty list when no data exists.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    events_q = (
        select(
            OrderEvent.order_id,
            OrderEvent.event_type,
            OrderEvent.occurred_at,
        )
        .where(
            OrderEvent.workspace_id == workspace_id,
            OrderEvent.occurred_at >= cutoff,
        )
        .order_by(OrderEvent.order_id, OrderEvent.occurred_at)
    )
    rows = (await db.execute(events_q)).all()

    if not rows:
        return []

    # Group by order_id
    orders: dict[str, list[tuple[str, datetime]]] = {}
    for row in rows:
        orders.setdefault(row.order_id, []).append((row.event_type, row.occurred_at))

    results = []
    for order_id, events in orders.items():
        phases = []
        for i in range(1, len(events)):
            prev_type, prev_at = events[i - 1]
            curr_type, curr_at = events[i]
            duration = (curr_at - prev_at).total_seconds()
            phases.append(
                {
                    "from": prev_type,
                    "to": curr_type,
                    "duration_seconds": round(duration, 2),
                }
            )
        results.append({"order_id": order_id, "phases": phases})

    return results


async def get_economic_health(
    db: AsyncSession,
    workspace_id: str,
    days: int = 30,
) -> dict:
    """Aggregate ledger and escrow statistics.

    Returns zero-valued metrics when no data exists.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # ── Ledger aggregates ──
    ledger_q = (
        select(
            func.coalesce(func.sum(LedgerEntry.amount), 0.0).label("total_volume"),
            func.coalesce(func.avg(LedgerEntry.amount), 0.0).label("avg_transaction_size"),
            func.count().label("transaction_count"),
        )
        .where(
            LedgerEntry.workspace_id == workspace_id,
            LedgerEntry.recorded_at >= cutoff,
        )
    )
    ledger_row = (await db.execute(ledger_q)).one()

    # ── Count by tx_type ──
    tx_type_q = (
        select(
            LedgerEntry.tx_type,
            func.count().label("count"),
        )
        .where(
            LedgerEntry.workspace_id == workspace_id,
            LedgerEntry.recorded_at >= cutoff,
        )
        .group_by(LedgerEntry.tx_type)
    )
    tx_type_rows = (await db.execute(tx_type_q)).all()
    tx_type_counts = {row.tx_type: int(row.count) for row in tx_type_rows}

    # ── Burn amount ──
    burn_q = (
        select(
            func.coalesce(func.sum(LedgerEntry.amount), 0.0).label("burn_amount"),
        )
        .where(
            LedgerEntry.workspace_id == workspace_id,
            LedgerEntry.tx_type == "burn",
            LedgerEntry.recorded_at >= cutoff,
        )
    )
    burn_row = (await db.execute(burn_q)).one()

    # ── Escrow utilization ──
    escrow_q = (
        select(
            func.count().label("total_escrow"),
            func.count(
                case(
                    (EscrowRecord.released.is_(True), EscrowRecord.id),
                    else_=None,
                )
            ).label("released_count"),
        )
        .where(
            EscrowRecord.workspace_id == workspace_id,
            EscrowRecord.created_at >= cutoff,
        )
    )
    escrow_row = (await db.execute(escrow_q)).one()

    total_escrow = int(escrow_row.total_escrow)
    released_count = int(escrow_row.released_count)
    escrow_utilization = (released_count / total_escrow) if total_escrow > 0 else 0.0

    return {
        "total_volume": round(float(ledger_row.total_volume), 2),
        "avg_transaction_size": round(float(ledger_row.avg_transaction_size), 2),
        "transaction_count": int(ledger_row.transaction_count),
        "tx_type_counts": tx_type_counts,
        "escrow_utilization": round(escrow_utilization, 4),
        "burn_amount": round(float(burn_row.burn_amount), 2),
    }
