"""Order read endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from mesh_platform.dependencies import DBSession, get_workspace
from mesh_platform.models.order import Order, OrderEvent
from mesh_platform.models.workspace import Workspace
from mesh_platform.schemas.order import OrderEventResponse, OrderListResponse, OrderResponse

router = APIRouter(tags=["orders"])


@router.get(
    "/workspaces/{workspace_id}/orders",
    response_model=OrderListResponse,
)
async def list_orders(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: DBSession,
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    q = select(Order).where(Order.workspace_id == workspace.id)
    if status:
        q = q.where(Order.current_status == status)
    q = q.order_by(Order.created_at.desc()).limit(limit).offset(offset)

    count_q = select(func.count()).select_from(Order).where(Order.workspace_id == workspace.id)
    if status:
        count_q = count_q.where(Order.current_status == status)

    result = await db.execute(q)
    total_result = await db.execute(count_q)
    return OrderListResponse(
        orders=list(result.scalars().all()),
        total=total_result.scalar_one(),
    )


@router.get(
    "/workspaces/{workspace_id}/orders/{order_id}",
    response_model=OrderResponse,
)
async def get_order(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    order_id: str,
    db: DBSession,
):
    from fastapi import HTTPException, status

    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.workspace_id == workspace.id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.get(
    "/workspaces/{workspace_id}/orders/{order_id}/events",
    response_model=list[OrderEventResponse],
)
async def list_order_events(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    order_id: str,
    db: DBSession,
):
    result = await db.execute(
        select(OrderEvent)
        .where(OrderEvent.order_id == order_id, OrderEvent.workspace_id == workspace.id)
        .order_by(OrderEvent.occurred_at)
    )
    return list(result.scalars().all())
