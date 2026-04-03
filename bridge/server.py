"""MQTT -> WebSocket bridge for the dashboard."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import paho.mqtt.client as mqtt
import websockets
from websockets.asyncio.server import serve

logger = logging.getLogger(__name__)

# Rate limit: max messages per second per client
MAX_MESSAGES_PER_SECOND = 60


class MQTTWebSocketBridge:
    """Bridges MQTT messages to WebSocket clients for the dashboard.

    Subscribes to mesh/# on FoxMQ, transforms messages,
    and broadcasts to all connected WebSocket clients.
    """

    def __init__(
        self,
        mqtt_host: str = "127.0.0.1",
        mqtt_port: int = 1883,
        mqtt_username: str = "",
        mqtt_password: str = "",
        ws_host: str = "0.0.0.0",
        ws_port: int = 8080,
    ) -> None:
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.ws_host = ws_host
        self.ws_port = ws_port

        self._clients: set[websockets.WebSocketServerProtocol] = set()
        self._message_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1000)
        self._mqtt_client: mqtt.Client | None = None
        self._mqtt_username = mqtt_username
        self._mqtt_password = mqtt_password

    def _setup_mqtt(self) -> None:
        """Configure and connect the MQTT client."""
        self._mqtt_client = mqtt.Client(
            client_id="mesh-bridge",
            protocol=mqtt.MQTTv5,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        if self._mqtt_username:
            self._mqtt_client.username_pw_set(self._mqtt_username, self._mqtt_password)

        self._mqtt_client.on_connect = self._on_mqtt_connect
        self._mqtt_client.on_message = self._on_mqtt_message

        self._mqtt_client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)
        self._mqtt_client.loop_start()

    def _on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.info("Bridge connected to FoxMQ at %s:%d", self.mqtt_host, self.mqtt_port)
            client.subscribe("mesh/#", qos=1)
        else:
            logger.error("Bridge MQTT connection failed: %s", reason_code)

    def _on_mqtt_message(self, client, userdata, message: mqtt.MQTTMessage):
        """Handle incoming MQTT message — queue for WebSocket broadcast."""
        try:
            payload = message.payload.decode("utf-8")
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                parsed = {"raw": payload}

            event = {
                "topic": message.topic,
                "timestamp": time.time(),
                "payload": parsed,
                "qos": message.qos,
                "retain": message.retain,
            }

            try:
                self._message_queue.put_nowait(event)
            except asyncio.QueueFull:
                pass  # Drop oldest if queue full (backpressure)

        except Exception:
            logger.exception("Error processing MQTT message")

    async def _ws_handler(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """Handle a WebSocket client connection."""
        self._clients.add(websocket)
        logger.info("Dashboard client connected (%d total)", len(self._clients))
        try:
            async for message in websocket:
                # Handle commands from dashboard (chaos controls, etc.)
                try:
                    cmd = json.loads(message)
                    await self._handle_dashboard_command(cmd)
                except json.JSONDecodeError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._clients.discard(websocket)
            logger.info("Dashboard client disconnected (%d remaining)", len(self._clients))

    async def _handle_dashboard_command(self, cmd: dict[str, Any]) -> None:
        """Process commands from the dashboard (e.g., chaos triggers)."""
        action = cmd.get("action")
        if action == "kill_agent" and self._mqtt_client:
            target = cmd.get("target", "")
            logger.info("Dashboard command: kill agent %s", target)
            # Publish a chaos command that agents can listen for
            self._mqtt_client.publish(
                "mesh/system/chaos",
                json.dumps({"action": "kill", "target": target}),
                qos=1,
            )

    async def _broadcaster(self) -> None:
        """Consume from queue and broadcast to all WebSocket clients."""
        while True:
            event = await self._message_queue.get()
            if not self._clients:
                continue

            data = json.dumps(event)
            dead_clients = set()
            for client in self._clients:
                try:
                    await client.send(data)
                except websockets.exceptions.ConnectionClosed:
                    dead_clients.add(client)
            self._clients -= dead_clients

    async def run(self) -> None:
        """Start the bridge: MQTT subscriber + WebSocket server."""
        self._setup_mqtt()
        logger.info("Bridge WebSocket server starting on %s:%d", self.ws_host, self.ws_port)

        # Start broadcaster task
        broadcaster_task = asyncio.create_task(self._broadcaster())

        async with serve(self._ws_handler, self.ws_host, self.ws_port):
            await asyncio.Future()  # Run forever


def main():
    import argparse

    parser = argparse.ArgumentParser(description="MESH MQTT-WebSocket Bridge")
    parser.add_argument("--mqtt-host", default="127.0.0.1")
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument("--mqtt-username", default="")
    parser.add_argument("--mqtt-password", default="")
    parser.add_argument("--ws-host", default="0.0.0.0")
    parser.add_argument("--ws-port", type=int, default=8080)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    bridge = MQTTWebSocketBridge(
        mqtt_host=args.mqtt_host,
        mqtt_port=args.mqtt_port,
        mqtt_username=args.mqtt_username,
        mqtt_password=args.mqtt_password,
        ws_host=args.ws_host,
        ws_port=args.ws_port,
    )
    asyncio.run(bridge.run())


if __name__ == "__main__":
    main()
