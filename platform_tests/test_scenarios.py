"""Tests for scenario CRUD router endpoints."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient

from platform_tests.conftest import auth_header, register_user

# ── Valid scenario definition fixture ──

VALID_DEFINITION = {
    "agents": [
        {"role": "buyer", "count": 1, "initial_balance": 5000, "capabilities": ["electronics"]},
        {"role": "supplier", "count": 2, "initial_balance": 5000, "capabilities": ["electronics"]},
    ],
    "goods": [
        {"name": "Laptop Display", "category": "electronics", "base_price": 100.0, "volatility": 0.1}
    ],
    "orders": [],
    "chaos_events": [],
}

VALID_SCENARIO_BODY = {
    "name": "Test Scenario",
    "description": "A test scenario",
    "duration_seconds": 120,
    "definition": VALID_DEFINITION,
}


@pytest_asyncio.fixture
async def owner_setup(client: AsyncClient):
    """Register a user, create a workspace, and return (token, workspace_id)."""
    tokens = await register_user(client, email="owner@mesh.io")
    token = tokens["access_token"]
    resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Scenario WS", "slug": "scenario-ws"},
        headers=auth_header(token),
    )
    assert resp.status_code == 201
    ws_id = resp.json()["id"]
    return token, ws_id


@pytest.mark.asyncio
async def test_create_scenario(client: AsyncClient, owner_setup):
    token, ws_id = owner_setup
    resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/scenarios",
        json=VALID_SCENARIO_BODY,
        headers=auth_header(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Scenario"
    assert data["description"] == "A test scenario"
    assert data["duration_seconds"] == 120
    assert data["workspace_id"] == ws_id
    assert data["is_system"] is False
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_scenarios(client: AsyncClient, owner_setup):
    token, ws_id = owner_setup
    # Create two scenarios
    await client.post(
        f"/api/v1/workspaces/{ws_id}/scenarios",
        json={**VALID_SCENARIO_BODY, "name": "Scenario A"},
        headers=auth_header(token),
    )
    await client.post(
        f"/api/v1/workspaces/{ws_id}/scenarios",
        json={**VALID_SCENARIO_BODY, "name": "Scenario B"},
        headers=auth_header(token),
    )
    resp = await client.get(
        f"/api/v1/workspaces/{ws_id}/scenarios",
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    scenarios = resp.json()["scenarios"]
    names = [s["name"] for s in scenarios]
    assert "Scenario A" in names
    assert "Scenario B" in names


@pytest.mark.asyncio
async def test_get_scenario_detail(client: AsyncClient, owner_setup):
    token, ws_id = owner_setup
    create_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/scenarios",
        json=VALID_SCENARIO_BODY,
        headers=auth_header(token),
    )
    scenario_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/workspaces/{ws_id}/scenarios/{scenario_id}",
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == scenario_id
    assert data["name"] == "Test Scenario"


@pytest.mark.asyncio
async def test_get_scenario_not_found(client: AsyncClient, owner_setup):
    token, ws_id = owner_setup
    resp = await client.get(
        f"/api/v1/workspaces/{ws_id}/scenarios/nonexistent-id",
        headers=auth_header(token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_scenario(client: AsyncClient, owner_setup):
    token, ws_id = owner_setup
    create_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/scenarios",
        json=VALID_SCENARIO_BODY,
        headers=auth_header(token),
    )
    scenario_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/workspaces/{ws_id}/scenarios/{scenario_id}",
        json={"name": "Updated Scenario", "duration_seconds": 300},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Scenario"
    assert data["duration_seconds"] == 300
    assert data["updated_at"] is not None


@pytest.mark.asyncio
async def test_update_scenario_not_found(client: AsyncClient, owner_setup):
    token, ws_id = owner_setup
    resp = await client.put(
        f"/api/v1/workspaces/{ws_id}/scenarios/nonexistent-id",
        json={"name": "Nope"},
        headers=auth_header(token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_scenario(client: AsyncClient, owner_setup):
    token, ws_id = owner_setup
    create_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/scenarios",
        json=VALID_SCENARIO_BODY,
        headers=auth_header(token),
    )
    scenario_id = create_resp.json()["id"]

    resp = await client.delete(
        f"/api/v1/workspaces/{ws_id}/scenarios/{scenario_id}",
        headers=auth_header(token),
    )
    assert resp.status_code == 204

    # Verify it's gone
    get_resp = await client.get(
        f"/api/v1/workspaces/{ws_id}/scenarios/{scenario_id}",
        headers=auth_header(token),
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_scenario_not_found(client: AsyncClient, owner_setup):
    token, ws_id = owner_setup
    resp = await client.delete(
        f"/api/v1/workspaces/{ws_id}/scenarios/nonexistent-id",
        headers=auth_header(token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_scenario_validation_rejects_no_buyer(client: AsyncClient, owner_setup):
    token, ws_id = owner_setup
    bad_body = {
        **VALID_SCENARIO_BODY,
        "definition": {
            "agents": [
                {"role": "supplier", "count": 1, "initial_balance": 5000, "capabilities": []},
            ],
            "goods": [{"name": "Widget", "category": "parts", "base_price": 10.0}],
        },
    }
    resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/scenarios",
        json=bad_body,
        headers=auth_header(token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_scenario_validation_rejects_no_goods(client: AsyncClient, owner_setup):
    token, ws_id = owner_setup
    bad_body = {
        **VALID_SCENARIO_BODY,
        "definition": {
            "agents": [
                {"role": "buyer", "count": 1, "initial_balance": 5000, "capabilities": []},
                {"role": "supplier", "count": 1, "initial_balance": 5000, "capabilities": []},
            ],
            "goods": [],
        },
    }
    resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/scenarios",
        json=bad_body,
        headers=auth_header(token),
    )
    assert resp.status_code == 422
