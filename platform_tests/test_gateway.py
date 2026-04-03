"""Tests for WebSocket gateway endpoint."""

from __future__ import annotations

import json

import pytest
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mesh_platform.models.base import Base
from mesh_platform.models.user import User, APIKey  # noqa: F401
from mesh_platform.models.workspace import Workspace, WorkspaceMembership  # noqa: F401
from mesh_platform.models.order import Order, OrderEvent  # noqa: F401
from mesh_platform.models.ledger import LedgerEntry, EscrowRecord  # noqa: F401
from mesh_platform.models.reputation import ReputationEvent, ReputationSnapshot  # noqa: F401
from mesh_platform.models.agent import AgentDefinition, AgentStatusLog  # noqa: F401
from mesh_platform.models.payment import PaymentIntent, PaymentWebhookEvent, Settlement  # noqa: F401


@pytest.fixture
def ws_test_app():
    """Create a fully self-contained test app for WebSocket testing."""
    from mesh_platform.dependencies import get_db
    from mesh_platform.gateway import connection_manager
    import mesh_platform.models.base as base_mod
    import mesh_platform.gateway.ws_endpoint as ws_ep_mod

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    original_factory = base_mod.async_session_factory
    base_mod.async_session_factory = test_session_factory

    original_tf = ws_ep_mod._transport_factory
    ws_ep_mod._transport_factory = lambda slug, agent_id: None

    from mesh_platform.app import create_app
    app = create_app(skip_lifespan=True)

    @app.on_event("startup")
    async def _create_test_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    connection_manager.clear_all()

    yield app

    base_mod.async_session_factory = original_factory
    ws_ep_mod._transport_factory = original_tf
    connection_manager.clear_all()


def _create_user_ws_key(tc, email="gwtest@mesh.io"):
    """Helper: register user, create workspace, create API key."""
    resp = tc.post("/api/v1/auth/register", json={
        "email": email, "password": "secret123", "display_name": "GW Tester",
    })
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = tc.post("/api/v1/workspaces", json={"name": "GW Test WS"}, headers=headers)
    assert resp.status_code == 201, resp.text
    ws_id = resp.json()["id"]

    resp = tc.post(f"/api/v1/workspaces/{ws_id}/api-keys", json={"name": "SDK Key"}, headers=headers)
    assert resp.status_code == 201, resp.text
    raw_key = resp.json()["raw_key"]

    return ws_id, raw_key


def test_gateway_rejects_missing_api_key(ws_test_app):
    from starlette.testclient import TestClient
    with TestClient(ws_test_app) as tc:
        with pytest.raises(Exception):
            with tc.websocket_connect("/ws/v1/agent"):
                pass


def test_gateway_rejects_invalid_api_key(ws_test_app):
    from starlette.testclient import TestClient
    with TestClient(ws_test_app) as tc:
        with tc.websocket_connect("/ws/v1/agent?api_key=amk_invalid_key_here") as ws:
            msg = json.loads(ws.receive_text())
            assert msg["type"] == "system"
            assert msg["event"] == "error"
            assert "Invalid" in msg["data"]["detail"]


def test_gateway_connect_and_register(ws_test_app):
    from starlette.testclient import TestClient
    with TestClient(ws_test_app) as tc:
        ws_id, raw_key = _create_user_ws_key(tc, email="gw1@mesh.io")
        with tc.websocket_connect(f"/ws/v1/agent?api_key={raw_key}") as ws:
            ws.send_text(json.dumps({
                "type": "register",
                "role": "supplier",
                "capabilities": ["electronics"],
                "balance": 5000,
            }))
            msg = json.loads(ws.receive_text())
            assert msg["type"] == "system"
            assert msg["event"] == "connected"
            assert "agent_id" in msg["data"]
            assert msg["data"]["workspace_id"] == ws_id


def test_gateway_subscribe_and_publish(ws_test_app):
    from starlette.testclient import TestClient
    with TestClient(ws_test_app) as tc:
        ws_id, raw_key = _create_user_ws_key(tc, email="gw2@mesh.io")
        with tc.websocket_connect(f"/ws/v1/agent?api_key={raw_key}") as ws:
            ws.send_text(json.dumps({"type": "register", "role": "buyer", "capabilities": []}))
            connected = json.loads(ws.receive_text())
            assert connected["event"] == "connected"

            ws.send_text(json.dumps({
                "type": "subscribe",
                "topics": ["orders/+/request", "orders/+/bid"],
            }))
            sub_resp = json.loads(ws.receive_text())
            assert sub_resp["event"] == "subscribed"
            assert "orders/+/request" in sub_resp["data"]["topics"]

            ws.send_text(json.dumps({
                "type": "publish",
                "topic": "orders/test-123/request",
                "payload": {"order_id": "test-123", "goods": "electronics", "quantity": 10},
            }))
            pub_resp = json.loads(ws.receive_text())
            assert pub_resp["event"] == "published"

            ws.send_text(json.dumps({"type": "ping"}))
            pong = json.loads(ws.receive_text())
            assert pong["type"] == "pong"


def test_gateway_register_required_first(ws_test_app):
    from starlette.testclient import TestClient
    with TestClient(ws_test_app) as tc:
        ws_id, raw_key = _create_user_ws_key(tc, email="gw3@mesh.io")
        with tc.websocket_connect(f"/ws/v1/agent?api_key={raw_key}") as ws:
            ws.send_text(json.dumps({"type": "subscribe", "topics": ["orders/+/request"]}))
            msg = json.loads(ws.receive_text())
            assert msg["event"] == "error"
            assert "register" in msg["data"]["detail"]


def test_gateway_connection_manager_tracking(ws_test_app):
    from mesh_platform.gateway import connection_manager
    from starlette.testclient import TestClient
    with TestClient(ws_test_app) as tc:
        ws_id, raw_key = _create_user_ws_key(tc, email="gw4@mesh.io")
        with tc.websocket_connect(f"/ws/v1/agent?api_key={raw_key}") as ws:
            ws.send_text(json.dumps({
                "type": "register",
                "role": "supplier",
                "capabilities": ["electronics"],
            }))
            connected = json.loads(ws.receive_text())
            assert connected["event"] == "connected"
            assert connection_manager.count(ws_id) == 1
        assert connection_manager.count(ws_id) == 0
