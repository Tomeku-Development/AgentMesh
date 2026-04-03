"""Payment endpoints: create payment + webhook receivers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from mesh_platform.dependencies import CurrentUser, DBSession, get_workspace
from mesh_platform.models.payment import PaymentIntent
from mesh_platform.models.workspace import Workspace
from mesh_platform.schemas.payment import CreatePaymentRequest, PaymentIntentResponse, PaymentListResponse
from mesh_platform.services.payment_service import create_payment_intent, get_provider, process_webhook

router = APIRouter(tags=["payments"])


@router.post(
    "/workspaces/{workspace_id}/payments",
    response_model=PaymentIntentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    body: CreatePaymentRequest,
    user: CurrentUser,
    db: DBSession,
):
    if body.provider not in ("xendit", "cryptomus"):
        raise HTTPException(status_code=400, detail="Provider must be 'xendit' or 'cryptomus'")
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    intent = await create_payment_intent(
        db,
        workspace_id=workspace.id,
        user_id=user.id,
        provider_name=body.provider,
        amount=body.amount,
        currency=body.currency,
    )
    return intent


@router.get(
    "/workspaces/{workspace_id}/payments",
    response_model=PaymentListResponse,
)
async def list_payments(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: DBSession,
):
    result = await db.execute(
        select(PaymentIntent)
        .where(PaymentIntent.workspace_id == workspace.id)
        .order_by(PaymentIntent.created_at.desc())
    )
    return PaymentListResponse(payments=list(result.scalars().all()))


@router.post("/webhooks/xendit")
async def xendit_webhook(request: Request, db: DBSession):
    body = await request.body()
    provider = get_provider("xendit")
    headers = dict(request.headers)

    if not provider.verify_webhook(headers, body):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    event = provider.parse_webhook(body)
    is_new = await process_webhook(db, "xendit", event)
    return {"processed": is_new}


@router.post("/webhooks/cryptomus")
async def cryptomus_webhook(request: Request, db: DBSession):
    body = await request.body()
    provider = get_provider("cryptomus")
    headers = dict(request.headers)

    if not provider.verify_webhook(headers, body):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    event = provider.parse_webhook(body)
    is_new = await process_webhook(db, "cryptomus", event)
    return {"processed": is_new}
