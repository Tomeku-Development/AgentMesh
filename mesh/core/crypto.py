"""HMAC-SHA256 message signing and verification for MQTT messages."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

# Shared secret for HMAC — in production, derived from agent keypairs via ECDH.
# For the hackathon demo, all agents share a pre-configured secret.
_DEFAULT_SECRET = b"mesh-vertex-swarm-2026"

# Message staleness threshold (seconds)
MESSAGE_MAX_AGE = 60.0

# Nonce cache size for replay protection
_NONCE_CACHE_SIZE = 10000


class ReplayDetector:
    """Detect replayed messages using a bounded nonce cache."""

    def __init__(self, max_size: int = _NONCE_CACHE_SIZE) -> None:
        self._seen: set[str] = set()
        self._max_size = max_size

    def check_and_record(self, nonce: str) -> bool:
        """Return True if nonce is new (not a replay). Records it."""
        if nonce in self._seen:
            return False
        if len(self._seen) >= self._max_size:
            # Evict oldest half — simple but effective for bounded memory
            to_keep = list(self._seen)[self._max_size // 2 :]
            self._seen = set(to_keep)
        self._seen.add(nonce)
        return True


def canonical_json(data: dict[str, Any]) -> str:
    """Produce canonical JSON: sorted keys, no whitespace, ensure_ascii."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sign_message(data: dict[str, Any], secret: bytes = _DEFAULT_SECRET) -> str:
    """Compute HMAC-SHA256 of canonical JSON representation. Returns hex digest."""
    canon = canonical_json(data)
    return hmac.new(secret, canon.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_signature(
    data: dict[str, Any], signature: str, secret: bytes = _DEFAULT_SECRET
) -> bool:
    """Verify HMAC-SHA256 signature against canonical JSON of data."""
    expected = sign_message(data, secret)
    return hmac.compare_digest(expected, signature)


def is_message_fresh(timestamp_iso: str, max_age: float = MESSAGE_MAX_AGE) -> bool:
    """Check if a message timestamp is within the acceptable age window."""
    from datetime import datetime, timezone

    try:
        msg_time = datetime.fromisoformat(timestamp_iso)
        if msg_time.tzinfo is None:
            msg_time = msg_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age = abs((now - msg_time).total_seconds())
        return age <= max_age
    except (ValueError, TypeError):
        return False
