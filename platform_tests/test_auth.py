"""Tests for auth endpoints: register, login, refresh, me."""

from __future__ import annotations

import pytest
from platform_tests.conftest import auth_header, register_user


@pytest.mark.asyncio
async def test_register_success(client):
    data = await register_user(client)
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await register_user(client, email="dup@mesh.io")
    resp = await client.post("/api/v1/auth/register", json={
        "email": "dup@mesh.io", "password": "pass", "display_name": "Dup",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    await register_user(client, email="login@mesh.io", password="mypass")
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@mesh.io", "password": "mypass",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await register_user(client, email="wrong@mesh.io", password="correct")
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wrong@mesh.io", "password": "incorrect",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    tokens = await register_user(client, email="refresh@mesh.io")
    resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_me_endpoint(client):
    tokens = await register_user(client, email="me@mesh.io", display_name="Me User")
    resp = await client.get("/api/v1/auth/me", headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 200
    user = resp.json()
    assert user["email"] == "me@mesh.io"
    assert user["display_name"] == "Me User"


@pytest.mark.asyncio
async def test_me_unauthorized(client):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401
