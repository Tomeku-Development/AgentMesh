"""Tests for MQTT event sink handlers and tenant resolver."""

from __future__ import annotations

import pytest
from platform_tests.conftest import auth_header, register_user
from mesh_platform.sink.tenant_resolver import resolve_tenant
from mesh_platform.sink.handlers import resolve_handler


# --- Tenant Resolver ---

def test_resolve_tenant_saas_mode():
    assert resolve_tenant("mesh/acme-corp/orders/123/request") == "acme-corp"


def test_resolve_tenant_demo_mode():
    assert resolve_tenant("mesh/orders/123/request") is None


def test_resolve_tenant_discovery():
    assert resolve_tenant("mesh/my-ws/discovery/announce") == "my-ws"
    assert resolve_tenant("mesh/discovery/announce") is None


def test_resolve_tenant_ledger():
    assert resolve_tenant("mesh/tenant1/ledger/transactions") == "tenant1"


def test_resolve_tenant_unknown():
    assert resolve_tenant("something/else") is None


# --- Handler Resolution ---

def test_resolve_handler_request():
    h = resolve_handler("mesh/acme/orders/123/request")
    assert h is not None
    assert h.__name__ == "handle_order_request"


def test_resolve_handler_bid():
    h = resolve_handler("mesh/orders/123/bid")
    assert h is not None
    assert h.__name__ == "handle_order_bid"


def test_resolve_handler_transactions():
    h = resolve_handler("mesh/acme/ledger/transactions")
    assert h is not None
    assert h.__name__ == "handle_ledger_transaction"


def test_resolve_handler_escrow():
    h = resolve_handler("mesh/acme/ledger/escrow")
    assert h is not None
    assert h.__name__ == "handle_ledger_escrow"


def test_resolve_handler_reputation():
    h = resolve_handler("mesh/acme/reputation/updates")
    assert h is not None
    assert h.__name__ == "handle_reputation_update"


def test_resolve_handler_heartbeat():
    h = resolve_handler("mesh/acme/discovery/heartbeat")
    assert h is not None
    assert h.__name__ == "handle_heartbeat"


def test_resolve_handler_unknown():
    assert resolve_handler("mesh/acme/something/random") is None


# --- Handler DB Integration ---

@pytest.mark.asyncio
async def test_handle_order_request_creates_row(db_session):
    from mesh_platform.sink.handlers import handle_order_request
    from mesh_platform.models.order import Order
    from sqlalchemy import select

    await handle_order_request(
        db_session,
        workspace_id="__demo__",
        payload={
            "order_id": "ord-001",
            "goods": "batteries",
            "quantity": 500,
            "max_price_per_unit": 12.50,
            "sender_id": "buyer01",
        },
        message_id="msg-001",
        topic="mesh/orders/ord-001/request",
    )
    await db_session.flush()

    result = await db_session.execute(select(Order).where(Order.id == "ord-001"))
    order = result.scalar_one()
    assert order.goods == "batteries"
    assert order.quantity == 500
    assert order.current_status == "requested"


@pytest.mark.asyncio
async def test_handle_ledger_transaction_creates_row(db_session):
    from mesh_platform.sink.handlers import handle_ledger_transaction
    from mesh_platform.models.ledger import LedgerEntry
    from sqlalchemy import select

    await handle_ledger_transaction(
        db_session,
        workspace_id="__demo__",
        payload={
            "tx_id": "tx-001",
            "tx_type": "transfer",
            "from_agent": "buyer01",
            "to_agent": "supplier01",
            "amount": 5000.00,
            "order_id": "ord-001",
        },
        message_id=None,
        topic="mesh/ledger/transactions",
    )
    await db_session.flush()

    result = await db_session.execute(select(LedgerEntry).where(LedgerEntry.tx_id == "tx-001"))
    entry = result.scalar_one()
    assert float(entry.amount) == 5000.00
    assert entry.from_agent == "buyer01"
