"""Message filtering and aggregation for the bridge."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any


class RateLimiter:
    """Token bucket rate limiter for WebSocket messages."""

    def __init__(self, max_per_second: int = 60) -> None:
        self._max = max_per_second
        self._tokens: float = max_per_second
        self._last_refill: float = time.time()

    def allow(self) -> bool:
        now = time.time()
        elapsed = now - self._last_refill
        self._tokens = min(self._max, self._tokens + elapsed * self._max)
        self._last_refill = now

        if self._tokens >= 1:
            self._tokens -= 1
            return True
        return False


class HeartbeatAggregator:
    """Aggregates heartbeat messages into periodic summaries."""

    def __init__(self, interval: float = 1.0) -> None:
        self._interval = interval
        self._last_emit: float = 0.0
        self._heartbeats: dict[str, dict[str, Any]] = {}

    def add(self, agent_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Add a heartbeat. Returns aggregated summary if interval elapsed, else None."""
        self._heartbeats[agent_id] = payload
        now = time.time()

        if now - self._last_emit >= self._interval:
            self._last_emit = now
            summary = {
                "type": "heartbeat_summary",
                "timestamp": now,
                "agents": dict(self._heartbeats),
                "count": len(self._heartbeats),
            }
            return summary
        return None


def should_aggregate(topic: str) -> bool:
    """Check if a topic should be aggregated rather than forwarded individually."""
    return "heartbeat" in topic
