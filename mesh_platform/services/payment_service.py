"""Payment flow orchestration."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.models.payment import PaymentIntent, PaymentWebhookEvent, Settlement
from mesh_platform.payments.base import PaymentProvider, WebhookEvent
from mesh_platform.payments.xendit import XenditProvider
from mesh_platform.payments.cryptomus import CryptomusProvider


def get_provider(name: str) -> PaymentProvider:
    if name == "xendit":
        return XenditProvider()
    elif name == "cryptomus":
        return CryptomusProvider()
    raise ValueError(f"Unknown provider: {name}")


async def create_payment_intent(
    db: AsyncSession,
    *,
    workspace_id: str,
    user_id: str,
    provider_name: str,
    amount: float,
    currency: str,
    metadata: dict | None = None,
) -> PaymentIntent:
    intent = PaymentIntent(
        workspace_id=workspace_id,
        user_id=user_id,
        provider=provider_name,
        amount=amount,
        currency=currency,
    )
    db.add(intent)
    await db.flush()

    provider = get_provider(provider_name)
    result = await provider.create_payment(
        amount=amount,
        currency=currency,
        metadata={
            "payment_intent_id": intent.id,
            **(metadata or {}),
        },
    )

    intent.provider_reference_id = result.provider_reference_id
    intent.payment_url = result.payment_url
    await db.flush()
    return intent


async def process_webhook(
    db: AsyncSession,
    provider_name: str,
    event: WebhookEvent,
) -> bool:
    """Process a verified webhook event. Returns True if new, False if duplicate."""
    # Idempotency check
    existing = await db.execute(
        select(PaymentWebhookEvent).where(PaymentWebhookEvent.webhook_id == event.webhook_id)
    )
    if existing.scalar_one_or_none() is not None:
        return False  # Already processed

    # Record webhook
    wh = PaymentWebhookEvent(
        provider=provider_name,
        webhook_id=event.webhook_id,
        payment_intent_id=event.payment_intent_id,
        raw_payload=str(event.raw_payload),
        processed=True,
    )
    db.add(wh)

    # Update payment intent
    if event.payment_intent_id:
        result = await db.execute(
            select(PaymentIntent).where(PaymentIntent.id == event.payment_intent_id)
        )
        intent = result.scalar_one_or_none()
        if intent:
            intent.status = event.status
            if event.status == "paid":
                intent.paid_at = datetime.now(timezone.utc)
                # Create settlement
                settlement = Settlement(
                    payment_intent_id=intent.id,
                    workspace_id=intent.workspace_id,
                    action="credit_workspace",
                    amount=float(intent.amount),
                )
                db.add(settlement)

    return True
