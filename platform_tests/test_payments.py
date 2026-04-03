"""Tests for payment endpoints and webhook processing."""

from __future__ import annotations

import base64
import hashlib
import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from platform_tests.conftest import auth_header, register_user
from mesh_platform.payments.base import PaymentResult, WebhookEvent


# ── helpers ──────────────────────────────────────────────────────────────

async def _setup_workspace(client: AsyncClient, token: str) -> str:
    """Create workspace, return workspace id."""
    resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Pay Test WS"},
        headers=auth_header(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


MOCK_PAYMENT_RESULT = PaymentResult(
    provider_reference_id="xendit-ref-001",
    payment_url="https://checkout.xendit.co/xyz",
    raw_response={"id": "xendit-ref-001", "invoice_url": "https://checkout.xendit.co/xyz"},
)


# ── create payment intent ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_payment_xendit(client):
    tokens = await register_user(client, email="pay1@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    with patch(
        "mesh_platform.services.payment_service.XenditProvider.create_payment",
        new_callable=AsyncMock,
        return_value=MOCK_PAYMENT_RESULT,
    ):
        resp = await client.post(
            f"/api/v1/workspaces/{ws_id}/payments",
            json={"provider": "xendit", "amount": 100000, "currency": "IDR"},
            headers=auth_header(tokens["access_token"]),
        )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["provider"] == "xendit"
    assert data["amount"] == 100000
    assert data["currency"] == "IDR"
    assert data["status"] == "pending"
    assert data["payment_url"] == "https://checkout.xendit.co/xyz"


@pytest.mark.asyncio
async def test_create_payment_cryptomus(client):
    tokens = await register_user(client, email="pay2@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    crypto_result = PaymentResult(
        provider_reference_id="crypto-uuid-001",
        payment_url="https://pay.cryptomus.com/pay/abc",
        raw_response={"uuid": "crypto-uuid-001", "url": "https://pay.cryptomus.com/pay/abc"},
    )

    with patch(
        "mesh_platform.services.payment_service.CryptomusProvider.create_payment",
        new_callable=AsyncMock,
        return_value=crypto_result,
    ):
        resp = await client.post(
            f"/api/v1/workspaces/{ws_id}/payments",
            json={"provider": "cryptomus", "amount": 50.00, "currency": "USDT"},
            headers=auth_header(tokens["access_token"]),
        )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["provider"] == "cryptomus"
    assert data["amount"] == 50.0
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_payment_invalid_provider(client):
    tokens = await register_user(client, email="pay3@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/payments",
        json={"provider": "stripe", "amount": 100, "currency": "USD"},
        headers=auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 400
    assert "Provider" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_payment_invalid_amount(client):
    tokens = await register_user(client, email="pay4@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/payments",
        json={"provider": "xendit", "amount": -50, "currency": "IDR"},
        headers=auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 400
    assert "positive" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_payment_unauthenticated(client):
    resp = await client.post(
        "/api/v1/workspaces/fake-id/payments",
        json={"provider": "xendit", "amount": 100, "currency": "IDR"},
    )
    assert resp.status_code in (401, 422)


# ── list payments ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_payments(client):
    tokens = await register_user(client, email="pay5@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    with patch(
        "mesh_platform.services.payment_service.XenditProvider.create_payment",
        new_callable=AsyncMock,
        return_value=MOCK_PAYMENT_RESULT,
    ):
        await client.post(
            f"/api/v1/workspaces/{ws_id}/payments",
            json={"provider": "xendit", "amount": 50000, "currency": "IDR"},
            headers=auth_header(tokens["access_token"]),
        )
        await client.post(
            f"/api/v1/workspaces/{ws_id}/payments",
            json={"provider": "xendit", "amount": 75000, "currency": "IDR"},
            headers=auth_header(tokens["access_token"]),
        )

    resp = await client.get(
        f"/api/v1/workspaces/{ws_id}/payments",
        headers=auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["payments"]) == 2


# ── xendit webhook ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_xendit_webhook_success(client):
    """Create a payment, then simulate a paid webhook."""
    tokens = await register_user(client, email="pay6@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    with patch(
        "mesh_platform.services.payment_service.XenditProvider.create_payment",
        new_callable=AsyncMock,
        return_value=MOCK_PAYMENT_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/workspaces/{ws_id}/payments",
            json={"provider": "xendit", "amount": 100000, "currency": "IDR"},
            headers=auth_header(tokens["access_token"]),
        )

    intent_id = create_resp.json()["id"]

    webhook_body = json.dumps({
        "id": "wh-xendit-001",
        "external_id": intent_id,
        "status": "PAID",
    }).encode()

    with patch(
        "mesh_platform.config.settings.xendit_webhook_token",
        "test-callback-token",
    ):
        resp = await client.post(
            "/api/v1/webhooks/xendit",
            content=webhook_body,
            headers={
                "content-type": "application/json",
                "x-callback-token": "test-callback-token",
            },
        )

    assert resp.status_code == 200, resp.text
    assert resp.json()["processed"] is True


@pytest.mark.asyncio
async def test_xendit_webhook_invalid_token(client):
    webhook_body = json.dumps({
        "id": "wh-xendit-bad",
        "external_id": "fake-intent",
        "status": "PAID",
    }).encode()

    with patch(
        "mesh_platform.config.settings.xendit_webhook_token",
        "correct-token",
    ):
        resp = await client.post(
            "/api/v1/webhooks/xendit",
            content=webhook_body,
            headers={
                "content-type": "application/json",
                "x-callback-token": "wrong-token",
            },
        )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_xendit_webhook_idempotency(client):
    """Duplicate webhook with same webhook_id should return processed=False."""
    tokens = await register_user(client, email="pay7@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    with patch(
        "mesh_platform.services.payment_service.XenditProvider.create_payment",
        new_callable=AsyncMock,
        return_value=MOCK_PAYMENT_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/workspaces/{ws_id}/payments",
            json={"provider": "xendit", "amount": 100000, "currency": "IDR"},
            headers=auth_header(tokens["access_token"]),
        )

    intent_id = create_resp.json()["id"]

    webhook_body = json.dumps({
        "id": "wh-xendit-dup",
        "external_id": intent_id,
        "status": "PAID",
    }).encode()

    with patch(
        "mesh_platform.config.settings.xendit_webhook_token",
        "test-token",
    ):
        resp1 = await client.post(
            "/api/v1/webhooks/xendit",
            content=webhook_body,
            headers={
                "content-type": "application/json",
                "x-callback-token": "test-token",
            },
        )
        assert resp1.json()["processed"] is True

        resp2 = await client.post(
            "/api/v1/webhooks/xendit",
            content=webhook_body,
            headers={
                "content-type": "application/json",
                "x-callback-token": "test-token",
            },
        )
        assert resp2.json()["processed"] is False


# ── cryptomus webhook ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cryptomus_webhook_success(client):
    tokens = await register_user(client, email="pay8@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    crypto_result = PaymentResult(
        provider_reference_id="crypto-uuid-002",
        payment_url="https://pay.cryptomus.com/pay/def",
        raw_response={},
    )

    with patch(
        "mesh_platform.services.payment_service.CryptomusProvider.create_payment",
        new_callable=AsyncMock,
        return_value=crypto_result,
    ):
        create_resp = await client.post(
            f"/api/v1/workspaces/{ws_id}/payments",
            json={"provider": "cryptomus", "amount": 25.0, "currency": "USDT"},
            headers=auth_header(tokens["access_token"]),
        )

    intent_id = create_resp.json()["id"]

    webhook_data = {
        "uuid": "wh-crypto-001",
        "order_id": intent_id,
        "status": "paid",
    }

    api_key = "test-crypto-api-key"

    with patch("mesh_platform.config.settings.cryptomus_api_key", api_key):
        encoded = base64.b64encode(
            json.dumps(webhook_data, sort_keys=True).encode()
        ).decode()
        sign = hashlib.md5((encoded + api_key).encode()).hexdigest()
        webhook_data["sign"] = sign

        resp = await client.post(
            "/api/v1/webhooks/cryptomus",
            content=json.dumps(webhook_data).encode(),
            headers={"content-type": "application/json"},
        )

    assert resp.status_code == 200, resp.text
    assert resp.json()["processed"] is True


@pytest.mark.asyncio
async def test_cryptomus_webhook_invalid_signature(client):
    webhook_data = {
        "uuid": "wh-crypto-bad",
        "order_id": "fake",
        "status": "paid",
        "sign": "invalid-signature",
    }

    with patch("mesh_platform.config.settings.cryptomus_api_key", "real-key"):
        resp = await client.post(
            "/api/v1/webhooks/cryptomus",
            content=json.dumps(webhook_data).encode(),
            headers={"content-type": "application/json"},
        )

    assert resp.status_code == 403
