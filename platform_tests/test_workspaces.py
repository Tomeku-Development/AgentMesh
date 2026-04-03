"""Tests for workspace CRUD endpoints."""

from __future__ import annotations

import pytest
from platform_tests.conftest import auth_header, register_user


@pytest.mark.asyncio
async def test_create_workspace(client):
    tokens = await register_user(client, email="ws@mesh.io")
    resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "My Supply Chain", "slug": "my-sc"},
        headers=auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 201
    ws = resp.json()
    assert ws["slug"] == "my-sc"
    assert ws["name"] == "My Supply Chain"
    assert ws["plan"] == "starter"
    assert ws["max_agents"] == 10


@pytest.mark.asyncio
async def test_create_workspace_auto_slug(client):
    tokens = await register_user(client, email="auto@mesh.io")
    resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Acme Corp Logistics"},
        headers=auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 201
    ws = resp.json()
    assert ws["slug"] == "acme-corp-logistics"


@pytest.mark.asyncio
async def test_duplicate_slug_rejected(client):
    tokens = await register_user(client, email="slug@mesh.io")
    headers = auth_header(tokens["access_token"])
    await client.post("/api/v1/workspaces", json={"name": "A", "slug": "dup-slug"}, headers=headers)
    resp = await client.post("/api/v1/workspaces", json={"name": "B", "slug": "dup-slug"}, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_workspaces(client):
    tokens = await register_user(client, email="list@mesh.io")
    headers = auth_header(tokens["access_token"])
    await client.post("/api/v1/workspaces", json={"name": "WS1", "slug": "ws1"}, headers=headers)
    await client.post("/api/v1/workspaces", json={"name": "WS2", "slug": "ws2"}, headers=headers)

    resp = await client.get("/api/v1/workspaces", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["workspaces"]) == 2


@pytest.mark.asyncio
async def test_get_workspace_by_id(client):
    tokens = await register_user(client, email="get@mesh.io")
    headers = auth_header(tokens["access_token"])
    create_resp = await client.post(
        "/api/v1/workspaces", json={"name": "Detail", "slug": "detail"}, headers=headers
    )
    ws_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["slug"] == "detail"


@pytest.mark.asyncio
async def test_workspace_access_denied_for_non_member(client):
    tokens1 = await register_user(client, email="owner@mesh.io")
    tokens2 = await register_user(client, email="other@mesh.io")

    create_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Private", "slug": "private"},
        headers=auth_header(tokens1["access_token"]),
    )
    ws_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/workspaces/{ws_id}",
        headers=auth_header(tokens2["access_token"]),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
