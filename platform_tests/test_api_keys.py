"""Tests for API key management endpoints."""

from __future__ import annotations

import pytest
from platform_tests.conftest import auth_header, register_user


# -- helpers ---------------------------------------------------------------

async def _setup_workspace(client, token):
    resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Key Test WS"},
        headers=auth_header(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# -- tests -----------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_api_key(client):
    tokens = await register_user(client, email="key1@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/api-keys",
        json={"name": "My SDK Key"},
        headers=auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "My SDK Key"
    assert data["raw_key"].startswith("amk_")
    assert len(data["raw_key"]) > 20
    assert data["key_prefix"] == data["raw_key"][:12]


@pytest.mark.asyncio
async def test_create_api_key_with_scopes(client):
    tokens = await register_user(client, email="key2@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/api-keys",
        json={"name": "Scoped Key", "scopes": ["read", "write"]},
        headers=auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 201
    assert resp.json()["scopes"] == "read,write"


@pytest.mark.asyncio
async def test_create_api_key_with_expiry(client):
    tokens = await register_user(client, email="key3@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/api-keys",
        json={"name": "Expiring Key", "expires_in_days": 30},
        headers=auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 201
    assert resp.json()["expires_at"] is not None


@pytest.mark.asyncio
async def test_list_api_keys(client):
    tokens = await register_user(client, email="key4@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    # Create two keys
    for name in ["Key A", "Key B"]:
        await client.post(
            f"/api/v1/workspaces/{ws_id}/api-keys",
            json={"name": name},
            headers=auth_header(tokens["access_token"]),
        )

    resp = await client.get(
        f"/api/v1/workspaces/{ws_id}/api-keys",
        headers=auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 200
    keys = resp.json()["keys"]
    assert len(keys) == 2
    # No raw_key in list response
    assert "raw_key" not in keys[0]


@pytest.mark.asyncio
async def test_revoke_api_key(client):
    tokens = await register_user(client, email="key5@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    create_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/api-keys",
        json={"name": "Revocable Key"},
        headers=auth_header(tokens["access_token"]),
    )
    key_id = create_resp.json()["id"]

    # Revoke
    resp = await client.delete(
        f"/api/v1/workspaces/{ws_id}/api-keys/{key_id}",
        headers=auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 204

    # Should no longer appear in list
    list_resp = await client.get(
        f"/api/v1/workspaces/{ws_id}/api-keys",
        headers=auth_header(tokens["access_token"]),
    )
    assert len(list_resp.json()["keys"]) == 0


@pytest.mark.asyncio
async def test_revoke_nonexistent_key(client):
    tokens = await register_user(client, email="key6@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    resp = await client.delete(
        f"/api/v1/workspaces/{ws_id}/api-keys/nonexistent-id",
        headers=auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_validate_api_key_service(client, db_session):
    """Test the validate_api_key service function directly."""
    from mesh_platform.services.api_key_service import generate_api_key, validate_api_key
    from platform_tests.conftest import register_user, auth_header

    tokens = await register_user(client, email="key7@mesh.io")
    ws_id = await _setup_workspace(client, tokens["access_token"])

    # Get user_id from /me
    me_resp = await client.get("/api/v1/auth/me", headers=auth_header(tokens["access_token"]))
    user_id = me_resp.json()["id"]

    raw_key, api_key = await generate_api_key(
        db_session, user_id=user_id, workspace_id=ws_id, name="Direct Test"
    )
    await db_session.commit()

    result = await validate_api_key(db_session, raw_key)
    assert result is not None
    key, user, workspace = result
    assert key.name == "Direct Test"
    assert user.email == "key7@mesh.io"
    assert workspace.id == ws_id


@pytest.mark.asyncio
async def test_validate_invalid_key(db_session):
    from mesh_platform.services.api_key_service import validate_api_key

    result = await validate_api_key(db_session, "amk_totally_fake_key")
    assert result is None

    result2 = await validate_api_key(db_session, "not_even_prefixed")
    assert result2 is None
