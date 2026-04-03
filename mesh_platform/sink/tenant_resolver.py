"""Extract tenant slug from MQTT topic prefix."""

from __future__ import annotations

import re

# SaaS mode: mesh/{tenant_slug}/orders/{id}/request
# Demo mode: mesh/orders/{id}/request (tenant=None)
_TENANT_RE = re.compile(r"^mesh/([^/]+)/(?:orders|ledger|reputation|discovery|health)/")
_DEMO_RE = re.compile(r"^mesh/(?:orders|ledger|reputation|discovery|health)/")


def resolve_tenant(topic: str) -> str | None:
    """Return tenant slug from topic, or None for demo mode."""
    m = _TENANT_RE.match(topic)
    if m:
        slug = m.group(1)
        # If the slug is a known domain keyword, this is demo mode
        if slug in ("orders", "ledger", "reputation", "discovery", "health"):
            return None
        return slug
    if _DEMO_RE.match(topic):
        return None
    return None
