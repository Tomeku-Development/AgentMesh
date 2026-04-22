"""Webhook management router — registration, delivery history, and inbound triggers."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from mesh_platform.dependencies import DBSession, require_workspace_operator, require_workspace_owner
from mesh_platform.models.workspace import WorkspaceMembership
from mesh_platform.schemas.order import OrderResponse
from mesh_platform.schemas.webhook import (
    DeliveryListResponse,
    InboundTriggerRequest,
    WebhookCreate,
    WebhookListResponse,
    WebhookResponse,
)
from mesh_platform.services.webhook_service import (
    delete_webhook,
    get_delivery_history,
    list_webhooks,
    register_webhook,
    trigger_inbound_order,
)

router = APIRouter(tags=["webhooks"])


@router.post(
    "/workspaces/{workspace_id}/webhooks",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook(
    body: WebhookCreate,
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_owner)],
    db: DBSession,
):
    """Register a new outbound webhook (owner only)."""
    webhook = await register_webhook(db, membership.workspace_id, body)
    # Deserialize event_types from JSON string for the response
    return WebhookResponse(
        id=webhook.id,
        workspace_id=webhook.workspace_id,
        url=webhook.url,
        event_types=json.loads(webhook.event_types),
        is_active=webhook.is_active,
        created_at=webhook.created_at,
    )


@router.get(
    "/workspaces/{workspace_id}/webhooks",
    response_model=WebhookListResponse,
)
async def list_all(
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_owner)],
    db: DBSession,
):
    """List all active webhooks for the workspace (owner only)."""
    webhooks = await list_webhooks(db, membership.workspace_id)
    return WebhookListResponse(
        webhooks=[
            WebhookResponse(
                id=w.id,
                workspace_id=w.workspace_id,
                url=w.url,
                event_types=json.loads(w.event_types),
                is_active=w.is_active,
                created_at=w.created_at,
            )
            for w in webhooks
        ]
    )


@router.delete(
    "/workspaces/{workspace_id}/webhooks/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_webhook(
    webhook_id: Annotated[str, Path()],
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_owner)],
    db: DBSession,
):
    """Delete a webhook registration (owner only)."""
    deleted = await delete_webhook(db, webhook_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
        )


@router.get(
    "/workspaces/{workspace_id}/webhooks/{webhook_id}/deliveries",
    response_model=DeliveryListResponse,
)
async def delivery_history(
    webhook_id: Annotated[str, Path()],
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_owner)],
    db: DBSession,
):
    """Get delivery history for a webhook (owner only)."""
    deliveries = await get_delivery_history(db, webhook_id)
    return DeliveryListResponse(deliveries=deliveries)


@router.post(
    "/workspaces/{workspace_id}/triggers/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def inbound_trigger(
    body: InboundTriggerRequest,
    membership: Annotated[WorkspaceMembership, Depends(require_workspace_operator)],
    db: DBSession,
):
    """Create an order from an external system trigger (operator+ access)."""
    order = await trigger_inbound_order(db, membership.workspace_id, body)
    return order
