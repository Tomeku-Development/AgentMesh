"""Per-connection agent session bridging WebSocket to MQTT.

NOTE: LLM usage tracking is handled via the LLMRouter.set_usage_callback()
mechanism. When the platform initializes the LLM router (typically in the
mesh agent initialization or platform bootstrap), it should set a callback
that records usage via usage_service.record_llm_usage(). This keeps the
gateway decoupled from LLM billing concerns.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import secrets
import uuid
from typing import Any

from mesh_platform.config import settings
from mesh_platform.gateway.protocol import (
    WSMessageMessage,
    WSPongMessage,
    WSPublishMessage,
    WSSubscribeMessage,
    WSSystemMessage,
    WSUnsubscribeMessage,
    parse_client_message,
)

logger = logging.getLogger(__name__)


class AgentSession:
    """Manages a single SDK agent's bridge between WebSocket and MQTT.

    For production, uses TenantTransport → MQTT.
    For testing, the transport can be replaced via the transport_factory kwarg.
    """

    def __init__(
        self,
        websocket: Any,
        workspace_id: str,
        workspace_slug: str,
        user_id: str,
        agent_id: str | None = None,
        agent_role: str = "buyer",
        capabilities: list[str] | None = None,
        transport_factory: Any = None,
    ):
        self.websocket = websocket
        self.workspace_id = workspace_id
        self.workspace_slug = workspace_slug
        self.user_id = user_id
        self.agent_id = agent_id or hashlib.sha256(secrets.token_bytes(32)).hexdigest()[:16]
        self.agent_role = agent_role
        self.capabilities = capabilities or []
        self._subscribed_topics: set[str] = set()
        self._transport: Any = None
        self._transport_factory = transport_factory
        self._heartbeat_task: asyncio.Task | None = None
        self._mqtt_connected = False
        self._hlc: Any = None

    async def start(self) -> None:
        """Initialize MQTT transport and start heartbeat."""
        try:
            if self._transport_factory:
                self._transport = self._transport_factory(self.workspace_slug, self.agent_id)
            else:
                self._connect_mqtt()

            # Send connected confirmation
            await self._send(WSSystemMessage(
                event="connected",
                data={
                    "agent_id": self.agent_id,
                    "workspace": self.workspace_slug,
                    "workspace_id": self.workspace_id,
                },
            ))
        except Exception as e:
            logger.error("AgentSession start failed: %s", e)
            await self._send(WSSystemMessage(event="error", data={"detail": str(e)}))
            raise

    def _connect_mqtt(self) -> None:
        """Connect to MQTT via TenantTransport (production path)."""
        from mesh.core.clock import HLC
        from mesh.core.config import MeshConfig

        from mesh_platform.tenant_agent import make_tenant_transport

        config = MeshConfig(
            broker_host=settings.mqtt_host,
            broker_port=settings.mqtt_port,
            agent_role=self.agent_role,
            agent_id=self.agent_id,
        )
        client_id = f"sdk-{self.workspace_slug}-{self.agent_id}"
        self._transport = make_tenant_transport(config, client_id, self.workspace_slug)
        self._hlc = HLC(self.agent_id)

        # Set callback for incoming MQTT messages
        self._transport.on_raw_message = self._on_mqtt_message
        self._transport.connect(blocking=True)
        self._mqtt_connected = True

        # Subscribe to discovery topics
        for topic in [
            "mesh/discovery/announce",
            "mesh/discovery/heartbeat",
            "mesh/discovery/goodbye",
            "mesh/health/alerts",
        ]:
            self._transport.subscribe(topic, qos=1)

    def _on_mqtt_message(self, topic: str, payload: bytes) -> None:
        """Callback when an MQTT message arrives. Forwards to WebSocket."""
        # Strip tenant prefix: mesh/{slug}/... -> ...
        clean_topic = self._strip_tenant_prefix(topic)
        try:
            data = json.loads(payload)
            # Extract header and payload from envelope if present
            header = data.get("header", {})
            msg_payload = data.get("payload", data)
        except (json.JSONDecodeError, AttributeError):
            header = {}
            msg_payload = {"raw": payload.decode("utf-8", errors="replace")}

        msg = WSMessageMessage(topic=clean_topic, payload=msg_payload, header=header)
        # Schedule the async send from the sync callback
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._send(msg))
        except RuntimeError:
            pass

    def _strip_tenant_prefix(self, topic: str) -> str:
        """mesh/{slug}/orders/123/bid -> orders/123/bid"""
        prefix = f"mesh/{self.workspace_slug}/"
        if topic.startswith(prefix):
            return topic[len(prefix):]
        if topic.startswith("mesh/"):
            return topic[5:]
        return topic

    async def handle_message(self, raw: str) -> None:
        """Handle a raw JSON message from the WebSocket client."""
        try:
            data = json.loads(raw)
            msg = parse_client_message(data)
        except (json.JSONDecodeError, ValueError) as e:
            await self._send(WSSystemMessage(event="error", data={"detail": str(e)}))
            return

        if isinstance(msg, WSSubscribeMessage):
            await self._handle_subscribe(msg)
        elif isinstance(msg, WSUnsubscribeMessage):
            await self._handle_unsubscribe(msg)
        elif isinstance(msg, WSPublishMessage):
            await self._handle_publish(msg)
        elif msg.type == "ping":
            await self._send(WSPongMessage())

    async def _handle_subscribe(self, msg: WSSubscribeMessage) -> None:
        for topic in msg.topics:
            if topic not in self._subscribed_topics:
                self._subscribed_topics.add(topic)
                if self._transport and hasattr(self._transport, "subscribe"):
                    self._transport.subscribe(f"mesh/{topic}", qos=1)
        await self._send(WSSystemMessage(
            event="subscribed",
            data={"topics": msg.topics},
        ))

    async def _handle_unsubscribe(self, msg: WSUnsubscribeMessage) -> None:
        for topic in msg.topics:
            self._subscribed_topics.discard(topic)
        await self._send(WSSystemMessage(
            event="unsubscribed",
            data={"topics": msg.topics},
        ))

    async def _handle_publish(self, msg: WSPublishMessage) -> None:
        if self._transport and self._mqtt_connected:
            from mesh.core.protocol import build_envelope

            secret = settings.gateway_hmac_secret.encode() if hasattr(settings, "gateway_hmac_secret") else b"mesh-vertex-swarm-2026"
            envelope = build_envelope(
                sender_id=self.agent_id,
                sender_role=self.agent_role,
                payload=msg.payload,
                hlc=self._hlc,
                secret=secret,
            )
            self._transport.publish(f"mesh/{msg.topic}", envelope, qos=1)

        # For non-MQTT mode (testing), just ack
        await self._send(WSSystemMessage(
            event="published",
            data={"topic": msg.topic},
        ))

    async def _send(self, msg: Any) -> None:
        """Send a message to the WebSocket client."""
        try:
            await self.websocket.send_text(msg.model_dump_json())
        except Exception:
            pass

    async def teardown(self) -> None:
        """Clean up MQTT connection and heartbeat."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

        if self._transport and self._mqtt_connected:
            try:
                from mesh.core.protocol import build_envelope
                from mesh.core.messages import Goodbye

                goodbye = Goodbye(agent_id=self.agent_id, reason="sdk_disconnect")
                envelope = build_envelope(self.agent_id, self.agent_role, goodbye, self._hlc)
                self._transport.publish("mesh/discovery/goodbye", envelope, qos=1)
                self._transport.disconnect()
            except Exception as e:
                logger.warning("Teardown error: %s", e)

        self._mqtt_connected = False
