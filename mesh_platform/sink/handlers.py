"""Per-topic persistence handlers for the MQTT event sink."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.models.order import Order, OrderEvent
from mesh_platform.models.ledger import LedgerEntry, EscrowRecord
from mesh_platform.models.reputation import ReputationEvent
from mesh_platform.models.agent import AgentDefinition, AgentStatusLog

logger = logging.getLogger(__name__)


async def handle_order_request(
    db: AsyncSession, workspace_id: str, payload: dict, message_id: str | None, topic: str
) -> None:
    order_id = payload.get("order_id", "")
    order = Order(
        id=order_id,
        workspace_id=workspace_id,
        goods=payload.get("goods", "unknown"),
        quantity=payload.get("quantity", 0),
        max_price_per_unit=payload.get("max_price_per_unit", 0),
        current_status="requested",
    )
    db.add(order)
    event = OrderEvent(
        order_id=order_id,
        workspace_id=workspace_id,
        event_type="request",
        agent_id=payload.get("sender_id", "unknown"),
        payload_json=json.dumps(payload),
        mqtt_message_id=message_id,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(event)


async def handle_order_bid(
    db: AsyncSession, workspace_id: str, payload: dict, message_id: str | None, topic: str
) -> None:
    order_id = payload.get("order_id", "")
    event = OrderEvent(
        order_id=order_id,
        workspace_id=workspace_id,
        event_type="bid",
        agent_id=payload.get("sender_id", "unknown"),
        payload_json=json.dumps(payload),
        mqtt_message_id=message_id,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.execute(
        update(Order).where(Order.id == order_id).values(bid_count=Order.bid_count + 1)
    )


async def handle_order_accept(
    db: AsyncSession, workspace_id: str, payload: dict, message_id: str | None, topic: str
) -> None:
    order_id = payload.get("order_id", "")
    event = OrderEvent(
        order_id=order_id,
        workspace_id=workspace_id,
        event_type="accept",
        agent_id=payload.get("sender_id", "unknown"),
        payload_json=json.dumps(payload),
        mqtt_message_id=message_id,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(
            winner_supplier_id=payload.get("winner_id"),
            agreed_price_per_unit=payload.get("agreed_price"),
            current_status="accepted",
        )
    )


async def handle_order_status(
    db: AsyncSession, workspace_id: str, payload: dict, message_id: str | None, topic: str
) -> None:
    order_id = payload.get("order_id", "")
    new_status = payload.get("status", "unknown")
    event = OrderEvent(
        order_id=order_id,
        workspace_id=workspace_id,
        event_type=new_status,
        agent_id=payload.get("sender_id", "unknown"),
        payload_json=json.dumps(payload),
        mqtt_message_id=message_id,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.execute(
        update(Order).where(Order.id == order_id).values(current_status=new_status)
    )


async def handle_ledger_transaction(
    db: AsyncSession, workspace_id: str, payload: dict, message_id: str | None, topic: str
) -> None:
    entry = LedgerEntry(
        tx_id=payload.get("tx_id", ""),
        workspace_id=workspace_id,
        tx_type=payload.get("tx_type", "transfer"),
        from_agent=payload.get("from_agent", ""),
        to_agent=payload.get("to_agent", ""),
        amount=payload.get("amount", 0),
        order_id=payload.get("order_id"),
        memo=payload.get("memo"),
        balance_after_from=payload.get("balance_after_from"),
        balance_after_to=payload.get("balance_after_to"),
    )
    db.add(entry)


async def handle_ledger_escrow(
    db: AsyncSession, workspace_id: str, payload: dict, message_id: str | None, topic: str
) -> None:
    action = payload.get("action", "lock")
    order_id = payload.get("order_id", "")
    if action == "lock":
        record = EscrowRecord(
            workspace_id=workspace_id,
            order_id=order_id,
            from_agent=payload.get("from_agent", ""),
            amount=payload.get("amount", 0),
        )
        db.add(record)
    elif action in ("release", "refund"):
        await db.execute(
            update(EscrowRecord)
            .where(EscrowRecord.order_id == order_id, EscrowRecord.workspace_id == workspace_id)
            .values(released=True, released_at=datetime.now(timezone.utc))
        )


async def handle_reputation_update(
    db: AsyncSession, workspace_id: str, payload: dict, message_id: str | None, topic: str
) -> None:
    event = ReputationEvent(
        workspace_id=workspace_id,
        subject_id=payload.get("subject_id", ""),
        capability=payload.get("capability", ""),
        old_score=payload.get("old_score", 0.5),
        new_score=payload.get("new_score", 0.5),
        reason=payload.get("reason", ""),
        evidence_order_id=payload.get("order_id"),
    )
    db.add(event)


async def handle_heartbeat(
    db: AsyncSession, workspace_id: str, payload: dict, message_id: str | None, topic: str
) -> None:
    agent_id = payload.get("agent_id", "")
    log = AgentStatusLog(
        agent_definition_id=agent_id,
        workspace_id=workspace_id,
        status=payload.get("state", "active"),
        load=payload.get("load", 0.0),
        active_orders=payload.get("active_orders", 0),
    )
    db.add(log)


# Topic pattern -> handler mapping
HANDLER_MAP: dict[str, callable] = {
    "request": handle_order_request,
    "bid": handle_order_bid,
    "accept": handle_order_accept,
    "status": handle_order_status,
    "transactions": handle_ledger_transaction,
    "escrow": handle_ledger_escrow,
    "updates": handle_reputation_update,
    "heartbeat": handle_heartbeat,
}


def resolve_handler(topic: str):
    """Return the appropriate handler for a given MQTT topic."""
    parts = topic.rstrip("/").split("/")
    if not parts:
        return None
    last = parts[-1]
    return HANDLER_MAP.get(last)
