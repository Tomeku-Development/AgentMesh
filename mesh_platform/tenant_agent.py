"""TenantBaseAgent: wraps BaseAgent with tenant-prefixed MQTT topics.

Dependency direction: mesh_platform -> mesh (never reverse).
"""

from __future__ import annotations

from mesh.core.config import MeshConfig
from mesh.core.transport import MeshTransport


class TenantTransport(MeshTransport):
    """MeshTransport wrapper that prepends a tenant slug to all topics."""

    def __init__(self, config: MeshConfig, client_id: str, tenant_slug: str, **kwargs):
        super().__init__(config, client_id, **kwargs)
        self.tenant_slug = tenant_slug

    def _tenant_topic(self, topic: str) -> str:
        """mesh/orders/123/request -> mesh/{slug}/orders/123/request"""
        if topic.startswith("mesh/"):
            return f"mesh/{self.tenant_slug}/{topic[5:]}"
        return f"mesh/{self.tenant_slug}/{topic}"

    def subscribe(self, topic: str, qos: int | None = None) -> None:
        super().subscribe(self._tenant_topic(topic), qos)

    def publish(self, topic: str, envelope, qos: int | None = None, retain: bool = False) -> None:
        super().publish(self._tenant_topic(topic), envelope, qos=qos, retain=retain)

    def publish_raw(self, topic: str, data: dict, qos: int = 1, retain: bool = False):
        super().publish_raw(self._tenant_topic(topic), data, qos, retain)


def make_tenant_transport(config: MeshConfig, client_id: str, tenant_slug: str) -> TenantTransport:
    """Factory for creating a tenant-isolated transport."""
    return TenantTransport(config, client_id, tenant_slug)
