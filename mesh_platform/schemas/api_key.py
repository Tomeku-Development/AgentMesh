"""Pydantic schemas for API key endpoints."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class CreateAPIKeyRequest(BaseModel):
    name: str = "Default"
    scopes: list[str] = []
    expires_in_days: int | None = None


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: str
    created_at: datetime
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    raw_key: str
    scopes: str
    created_at: datetime
    expires_at: datetime | None = None


class APIKeyListResponse(BaseModel):
    keys: list[APIKeyResponse]
