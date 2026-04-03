"""Xendit fiat payment provider (IDR, PHP, THB, VND, MYR)."""

from __future__ import annotations

import hmac
import json
from typing import Any

import httpx

from mesh_platform.config import settings
from mesh_platform.payments.base import PaymentProvider, PaymentResult, WebhookEvent


class XenditProvider(PaymentProvider):
    BASE_URL = "https://api.xendit.co"

    async def create_payment(
        self, amount: float, currency: str, metadata: dict[str, Any]
    ) -> PaymentResult:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/v2/invoices",
                json={
                    "external_id": metadata.get("payment_intent_id", ""),
                    "amount": amount,
                    "currency": currency,
                    "description": metadata.get("description", "MESH Platform Credit"),
                    "success_redirect_url": metadata.get("success_url", ""),
                    "failure_redirect_url": metadata.get("failure_url", ""),
                },
                auth=(settings.xendit_secret_key, ""),
            )
            resp.raise_for_status()
            data = resp.json()

        return PaymentResult(
            provider_reference_id=data["id"],
            payment_url=data["invoice_url"],
            raw_response=data,
        )

    def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        token = headers.get("x-callback-token", "")
        return hmac.compare_digest(token, settings.xendit_webhook_token)

    def parse_webhook(self, body: bytes) -> WebhookEvent:
        data = json.loads(body)
        status_map = {"PAID": "paid", "EXPIRED": "expired"}
        return WebhookEvent(
            webhook_id=data.get("id", ""),
            payment_intent_id=data.get("external_id"),
            status=status_map.get(data.get("status", ""), "failed"),
            raw_payload=data,
        )
