"""Webhook service — registration, delivery, dispatch, and inbound triggers."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.models.order import Order
from mesh_platform.models.webhook import WebhookDelivery, WebhookRegistration
from mesh_platform.schemas.webhook import InboundTriggerRequest, WebhookCreate


# Retry delays in seconds for exponential backoff (Requirement 2.3)
RETRY_DELAYS = [10, 30, 90]
MAX_ATTEMPTS = 3


def _compute_signature(secret: str, body: str) -> str:
    """Compute HMAC-SHA256 signature for webhook payload (Requirement 2.2)."""
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


async def register_webhook(
    db: AsyncSession,
    workspace_id: str,
    data: WebhookCreate,
) -> WebhookRegistration:
    """Register a new outbound webhook for a workspace (Requirement 2.1)."""
    webhook = WebhookRegistration(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        url=data.url,
        event_types=json.dumps(data.event_types),
        secret=data.secret,
        is_active=True,
    )
    db.add(webhook)
    await db.flush()
    return webhook


async def list_webhooks(
    db: AsyncSession,
    workspace_id: str,
) -> list[WebhookRegistration]:
    """List all active webhooks for a workspace (Requirement 2.7)."""
    result = await db.execute(
        select(WebhookRegistration).where(
            WebhookRegistration.workspace_id == workspace_id,
            WebhookRegistration.is_active.is_(True),
        )
    )
    return list(result.scalars().all())


async def delete_webhook(
    db: AsyncSession,
    webhook_id: str,
) -> bool:
    """Delete a webhook registration. Returns True if deleted, False if not found."""
    result = await db.execute(
        select(WebhookRegistration).where(WebhookRegistration.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()
    if webhook is None:
        return False
    await db.delete(webhook)
    await db.flush()
    return True


async def get_delivery_history(
    db: AsyncSession,
    webhook_id: str,
    limit: int = 100,
) -> list[WebhookDelivery]:
    """Get the last N delivery attempts for a webhook (Requirement 2.7)."""
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def _deliver_webhook(
    db: AsyncSession,
    webhook: WebhookRegistration,
    event_type: str,
    payload: dict,
) -> WebhookDelivery:
    """Deliver a single webhook with retry logic (Requirements 2.2, 2.3, 2.4).

    Creates a WebhookDelivery record, fires httpx.post with HMAC-SHA256 signature,
    and retries up to MAX_ATTEMPTS times with exponential backoff on failure.
    """
    body = json.dumps(payload)
    signature = _compute_signature(webhook.secret, body)

    headers = {
        "Content-Type": "application/json",
        "X-Mesh-Signature": f"sha256={signature}",
    }

    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event_type=event_type,
        payload_json=body,
        status="pending",
        attempt_number=1,
    )
    db.add(delivery)
    await db.flush()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        delivery.attempt_number = attempt
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook.url, content=body, headers=headers)

            delivery.http_status_code = response.status_code
            # Truncate response body to 1000 chars
            delivery.response_body = response.text[:1000] if response.text else None

            if 200 <= response.status_code < 300:
                delivery.status = "success"
                delivery.delivered_at = datetime.now(timezone.utc)
                await db.flush()
                return delivery

        except Exception as exc:
            delivery.http_status_code = None
            delivery.response_body = str(exc)[:1000]

        # If we haven't succeeded and have more attempts, wait with backoff
        if attempt < MAX_ATTEMPTS:
            import asyncio

            delay = RETRY_DELAYS[attempt - 1] if attempt - 1 < len(RETRY_DELAYS) else 90
            await asyncio.sleep(delay)

    # All attempts exhausted — mark as permanently failed (Requirement 2.4)
    delivery.status = "failed"
    await db.flush()
    return delivery


async def dispatch_event(
    db: AsyncSession,
    workspace_id: str,
    event_type: str,
    payload: dict,
) -> list[WebhookDelivery]:
    """Dispatch an event to all matching webhooks for a workspace (Requirement 2.2).

    Queries active webhooks whose event_types list contains the given event_type,
    then delivers the payload to each matching webhook.
    """
    result = await db.execute(
        select(WebhookRegistration).where(
            WebhookRegistration.workspace_id == workspace_id,
            WebhookRegistration.is_active.is_(True),
        )
    )
    webhooks = result.scalars().all()

    deliveries: list[WebhookDelivery] = []
    for webhook in webhooks:
        # Check if this webhook subscribes to the event type
        registered_types = json.loads(webhook.event_types)
        if event_type not in registered_types:
            continue

        delivery = await _deliver_webhook(db, webhook, event_type, payload)
        deliveries.append(delivery)

    return deliveries


async def trigger_inbound_order(
    db: AsyncSession,
    workspace_id: str,
    data: InboundTriggerRequest,
) -> Order:
    """Create an Order record from an inbound trigger (Requirement 2.5).

    In production this would also publish an MQTT message to
    mesh/{slug}/orders/+/request, but for the MVP we just create the DB record.
    """
    order = Order(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        goods=data.goods,
        quantity=data.quantity,
        max_price_per_unit=data.max_price_per_unit,
        current_status="requested",
    )
    db.add(order)
    await db.flush()
    return order
