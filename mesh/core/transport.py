"""MQTT transport layer wrapping paho-mqtt with reconnection and QoS."""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Callable

import paho.mqtt.client as mqtt

from mesh.core.config import MeshConfig
from mesh.core.messages import MessageEnvelope
from mesh.core.protocol import deserialize_envelope, serialize_envelope
from mesh.core.topics import qos_for_topic

logger = logging.getLogger(__name__)

MessageHandler = Callable[[str, MessageEnvelope], None]


class MeshTransport:
    """MQTT transport for MESH agents using paho-mqtt MQTTv5."""

    def __init__(
        self,
        config: MeshConfig,
        client_id: str,
        on_envelope: MessageHandler | None = None,
    ) -> None:
        self.config = config
        self.client_id = client_id
        self._on_envelope = on_envelope
        self._connected = threading.Event()
        self._subscriptions: list[tuple[str, int]] = []
        self._raw_handlers: dict[str, Callable[[str, bytes], None]] = {}

        self._client = mqtt.Client(
            client_id=client_id,
            protocol=mqtt.MQTTv5,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        if config.broker_username:
            self._client.username_pw_set(config.broker_username, config.broker_password)

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

        # Reconnect settings
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)

    def connect(self, blocking: bool = True) -> None:
        """Connect to the FoxMQ broker."""
        logger.info(
            "Connecting to %s:%d as %s",
            self.config.broker_host,
            self.config.broker_port,
            self.client_id,
        )
        self._client.connect(
            self.config.broker_host,
            self.config.broker_port,
            keepalive=60,
        )
        if blocking:
            self._client.loop_start()
            self._connected.wait(timeout=10)
            if not self._connected.is_set():
                raise ConnectionError("Failed to connect to FoxMQ broker")
        else:
            self._client.loop_start()

    def disconnect(self) -> None:
        """Disconnect from the broker."""
        self._client.loop_stop()
        self._client.disconnect()
        self._connected.clear()

    def subscribe(self, topic: str, qos: int | None = None) -> None:
        """Subscribe to a topic. Re-subscribes on reconnect."""
        if qos is None:
            qos = qos_for_topic(topic)
        self._subscriptions.append((topic, qos))
        if self._connected.is_set():
            self._client.subscribe(topic, qos=qos)

    def publish(
        self,
        topic: str,
        envelope: MessageEnvelope,
        qos: int | None = None,
        retain: bool = False,
    ) -> None:
        """Publish a signed envelope to a topic."""
        if qos is None:
            qos = qos_for_topic(topic)
        payload = serialize_envelope(envelope)
        self._client.publish(topic, payload, qos=qos, retain=retain)
        logger.debug("PUB %s qos=%d len=%d", topic, qos, len(payload))

    def publish_raw(self, topic: str, data: dict[str, Any], qos: int = 1, retain: bool = False):
        """Publish a raw dict as JSON (for simple messages that don't need envelopes)."""
        payload = json.dumps(data)
        self._client.publish(topic, payload, qos=qos, retain=retain)

    def wait_for_connection(self, timeout: float = 10.0) -> bool:
        """Wait until connected. Returns True if connected."""
        return self._connected.wait(timeout=timeout)

    @property
    def is_connected(self) -> bool:
        return self._connected.is_set()

    # ── Internal callbacks ─────────────────────────────

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.info("Connected to FoxMQ broker")
            self._connected.set()
            # Re-subscribe to all topics
            for topic, qos in self._subscriptions:
                self._client.subscribe(topic, qos=qos)
        else:
            logger.error("Connection failed: %s", reason_code)

    def _on_message(self, client, userdata, message: mqtt.MQTTMessage):
        topic = message.topic
        payload = message.payload

        # Try to deliver as raw handler first
        for pattern, handler in self._raw_handlers.items():
            if mqtt.topic_matches_sub(pattern, topic):
                try:
                    handler(topic, payload)
                except Exception:
                    logger.exception("Raw handler error on %s", topic)
                return

        # Try to parse as envelope
        if self._on_envelope:
            try:
                envelope = deserialize_envelope(payload)
                self._on_envelope(topic, envelope)
            except Exception:
                logger.debug("Non-envelope message on %s (len=%d)", topic, len(payload))

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self._connected.clear()
        if reason_code == 0:
            logger.info("Disconnected cleanly")
        else:
            logger.warning("Unexpected disconnect: %s — will reconnect", reason_code)

    def add_raw_handler(self, topic_pattern: str, handler: Callable[[str, bytes], None]):
        """Register a raw bytes handler for a topic pattern (bypasses envelope parsing)."""
        self._raw_handlers[topic_pattern] = handler
