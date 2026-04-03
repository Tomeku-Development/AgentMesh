"""Cryptomus crypto payment provider (BTC, ETH, USDT, SOL, 150+ tokens)."""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

import httpx

from mesh_platform.config import settings
from mesh_platform.payments.base import PaymentProvider, PaymentResult, WebhookEvent


class CryptomusProvider(PaymentProvider):
    BASE_URL = "https://api.cryptomus.com/v1"

    def _sign(self, payload: dict) -> str:
        """MD5(base64(json_sorted) + api_key)."""
        encoded = base64.b64encode(
            json.dumps(payload, sort_keys=True).encode()
        ).decode()
        return hashlib.md5(
            (encoded + settings.cryptomus_api_key).encode()
        ).hexdigest()

    async def create_payment(
        self, amount: float, currency: str, metadata: dict[str, Any]
    ) -> PaymentResult:
        payload = {
            "amount": str(amount),
            "currency": currency,
            "order_id": metadata.get("payment_intent_id", ""),
            "url_callback": metadata.get("webhook_url", ""),
            "url_return": metadata.get("success_url", ""),
        }
        sign = self._sign(payload)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/payment",
                json=payload,
                headers={
                    "merchant": settings.cryptomus_merchant_id,
                    "sign": sign,
                },
            )
            resp.raise_for_status()
            data = resp.json().get("result", {})

        return PaymentResult(
            provider_reference_id=data.get("uuid", ""),
            payment_url=data.get("url", ""),
            raw_response=data,
        )

    def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        data = json.loads(body)
        received_sign = data.pop("sign", "")
        expected_sign = self._sign(data)
        return received_sign == expected_sign

    def parse_webhook(self, body: bytes) -> WebhookEvent:
        data = json.loads(body)
        status_map = {
            "paid": "paid",
            "paid_over": "paid",
            "wrong_amount": "failed",
            "cancel": "expired",
            "fail": "failed",
        }
        return WebhookEvent(
            webhook_id=data.get("uuid", ""),
            payment_intent_id=data.get("order_id"),
            status=status_map.get(data.get("status", ""), "failed"),
            raw_payload=data,
        )
