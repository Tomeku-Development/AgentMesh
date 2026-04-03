"""MQTT Event Sink: subscribes to mesh/# and persists events to PostgreSQL."""

from __future__ import annotations

import asyncio
import json
import logging

import paho.mqtt.client as mqtt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from mesh_platform.models.base import async_session_factory
from mesh_platform.sink.handlers import resolve_handler
from mesh_platform.sink.tenant_resolver import resolve_tenant
from mesh_platform.config import settings

logger = logging.getLogger(__name__)


class MQTTEventSink:
    """Standalone process that subscribes to mesh/# and writes events to PG."""

    def __init__(self, session_factory: async_sessionmaker | None = None):
        self.session_factory = session_factory or async_session_factory
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client: mqtt.Client | None = None

    def start(self) -> None:
        """Connect to MQTT broker and start the event loop."""
        self._loop = asyncio.new_event_loop()
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="mesh-sink")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        logger.info("Connecting to MQTT %s:%d", settings.mqtt_host, settings.mqtt_port)
        self._client.connect(settings.mqtt_host, settings.mqtt_port)
        self._client.loop_forever()

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        logger.info("Connected to MQTT, subscribing to mesh/#")
        client.subscribe("mesh/#", qos=1)

    def _on_message(self, client, userdata, msg):
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._process(msg), self._loop)

    async def _process(self, msg) -> None:
        topic = msg.topic
        handler = resolve_handler(topic)
        if handler is None:
            return

        tenant_slug = resolve_tenant(topic)

        try:
            payload = json.loads(msg.payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Invalid JSON on topic %s", topic)
            return

        message_id = payload.get("header", {}).get("message_id")

        # Resolve workspace_id from tenant slug
        workspace_id = tenant_slug or "__demo__"

        async with self.session_factory() as session:
            try:
                await handler(session, workspace_id, payload, message_id, topic)
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception("Failed to process message on %s", topic)


def run_sink():
    """Entry point for the sink process."""
    logging.basicConfig(level=logging.INFO)
    sink = MQTTEventSink()
    sink.start()


if __name__ == "__main__":
    run_sink()
