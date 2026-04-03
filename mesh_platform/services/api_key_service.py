"""API key generation, validation, and management."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.models.user import APIKey, User
from mesh_platform.models.workspace import Workspace


_PREFIX = "amk_"


def _generate_raw_key() -> tuple[str, str]:
    """Generate a raw API key and its prefix for lookup.

    Returns (raw_key, prefix) where prefix = first 8 chars after 'amk_'.
    """
    token = secrets.token_urlsafe(32)
    raw_key = f"{_PREFIX}{token}"
    prefix = raw_key[: len(_PREFIX) + 8]
    return raw_key, prefix


async def generate_api_key(
    db: AsyncSession,
    *,
    user_id: str,
    workspace_id: str,
    name: str = "Default",
    scopes: str = "",
    expires_in_days: int | None = None,
) -> tuple[str, APIKey]:
    """Create a new API key. Returns (raw_key_shown_once, api_key_row)."""
    raw_key, prefix = _generate_raw_key()
    key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()

    expires_at = None
    if expires_in_days is not None and expires_in_days > 0:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    api_key = APIKey(
        user_id=user_id,
        workspace_id=workspace_id,
        name=name,
        key_hash=key_hash,
        key_prefix=prefix,
        scopes=scopes,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.flush()
    return raw_key, api_key


async def validate_api_key(
    db: AsyncSession,
    raw_key: str,
) -> tuple[APIKey, User, Workspace] | None:
    """Validate a raw API key string. Returns (key, user, workspace) or None."""
    if not raw_key.startswith(_PREFIX):
        return None

    prefix = raw_key[: len(_PREFIX) + 8]

    result = await db.execute(
        select(APIKey).where(APIKey.key_prefix == prefix, APIKey.revoked == False)  # noqa: E712
    )
    candidates = result.scalars().all()

    for key in candidates:
        if bcrypt.checkpw(raw_key.encode(), key.key_hash.encode()):
            # Check expiry
            if key.expires_at and key.expires_at < datetime.now(timezone.utc):
                return None

            # Resolve user + workspace
            user_result = await db.execute(select(User).where(User.id == key.user_id))
            user = user_result.scalar_one_or_none()
            if user is None or not user.is_active:
                return None

            ws_result = await db.execute(select(Workspace).where(Workspace.id == key.workspace_id))
            workspace = ws_result.scalar_one_or_none()
            if workspace is None:
                return None

            # Update last_used_at
            key.last_used_at = datetime.now(timezone.utc)
            return key, user, workspace

    return None


async def list_api_keys(
    db: AsyncSession,
    workspace_id: str,
) -> list[APIKey]:
    """List all non-revoked API keys for a workspace."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.workspace_id == workspace_id, APIKey.revoked == False)  # noqa: E712
        .order_by(APIKey.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_api_key(
    db: AsyncSession,
    key_id: str,
    workspace_id: str,
) -> bool:
    """Revoke an API key. Returns True if found and revoked."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.workspace_id == workspace_id)
    )
    key = result.scalar_one_or_none()
    if key is None:
        return False
    key.revoked = True
    return True
