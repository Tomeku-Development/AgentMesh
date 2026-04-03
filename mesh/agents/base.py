"""Base agent ABC defining the lifecycle for all MESH agents."""

from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod

from mesh.core.clock import HLC
from mesh.core.config import MeshConfig
from mesh.core.identity import AgentIdentity
from mesh.core.ledger import Ledger
from mesh.core.messages import (
    DiscoveryAnnounce,
    Goodbye,
    Heartbeat,
    MessageEnvelope,
)
from mesh.core.protocol import build_envelope, deserialize_envelope, verify_envelope
from mesh.core.registry import PeerRegistry
from mesh.core.reputation import ReputationEngine
from mesh.core.state import AgentState, StateMachine
from mesh.core.topics import (
    DISCOVERY_ANNOUNCE,
    DISCOVERY_GOODBYE,
    DISCOVERY_HEARTBEAT,
    HEALTH_ALERTS,
    MESH_WILDCARD,
)
from mesh.core.transport import MeshTransport

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base for all MESH supply chain agents.

    Provides:
    - Identity (Ed25519)
    - MQTT transport with reconnect
    - Heartbeat loop
    - Peer discovery
    - State machine
    - Shared ledger and reputation engine
    """

    def __init__(
        self,
        config: MeshConfig,
        identity: AgentIdentity | None = None,
        ledger: Ledger | None = None,
        reputation: ReputationEngine | None = None,
    ) -> None:
        self.config = config
        self.identity = identity or AgentIdentity.generate()

        agent_id = config.agent_id
        if agent_id == "auto":
            agent_id = self.identity.agent_id
        self.agent_id = agent_id

        self.role = config.agent_role
        self.capabilities = config.get_capabilities()

        self.state_machine = StateMachine()
        self.registry = PeerRegistry(
            suspect_threshold=config.suspect_threshold,
            dead_threshold=config.dead_threshold,
        )
        self.ledger = ledger or Ledger()
        self.reputation = reputation or ReputationEngine()
        self.hlc = HLC.create(self.agent_id)

        self.transport = MeshTransport(
            config=config,
            client_id=self.agent_id,
            on_envelope=self._dispatch_envelope,
        )

        self._start_time = time.time()
        self._heartbeat_thread: threading.Thread | None = None
        self._liveness_thread: threading.Thread | None = None
        self._running = False
        self._active_orders: int = 0

    # ── Lifecycle ──────────────────────────────────────

    def start(self) -> None:
        """Connect to FoxMQ and begin operating."""
        logger.info("[%s] Starting %s agent (%s)", self.agent_id, self.role, self.agent_id)
        self._running = True

        # Connect to broker
        self.transport.connect(blocking=True)

        # Subscribe to common topics
        self.transport.subscribe(DISCOVERY_ANNOUNCE, qos=1)
        self.transport.subscribe(DISCOVERY_HEARTBEAT, qos=0)
        self.transport.subscribe(DISCOVERY_GOODBYE, qos=1)
        self.transport.subscribe(HEALTH_ALERTS, qos=1)

        # Subscribe to role-specific topics
        self._subscribe_topics()

        # Register self in reputation engine
        self.reputation.register(self.agent_id, self.role, self.capabilities)

        # Initialize balance
        self.ledger.init_balance(self.agent_id, self.config.initial_balance)

        # Transition to active
        self.state_machine.transition(AgentState.ACTIVE)

        # Announce presence
        self._announce()

        # Start heartbeat loop
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True, name=f"{self.agent_id}-heartbeat"
        )
        self._heartbeat_thread.start()

        # Start liveness checker
        self._liveness_thread = threading.Thread(
            target=self._liveness_loop, daemon=True, name=f"{self.agent_id}-liveness"
        )
        self._liveness_thread.start()

        # Agent-specific initialization
        self._on_start()

        logger.info("[%s] Agent started and active", self.agent_id)

    def stop(self) -> None:
        """Graceful shutdown."""
        logger.info("[%s] Shutting down", self.agent_id)
        self._running = False

        # Publish goodbye
        goodbye = Goodbye(agent_id=self.agent_id, reason="graceful_shutdown")
        envelope = build_envelope(self.agent_id, self.role, goodbye, self.hlc)
        self.transport.publish(DISCOVERY_GOODBYE, envelope)

        time.sleep(0.5)  # Let goodbye propagate
        self.state_machine.transition(AgentState.SHUTDOWN)
        self._on_stop()
        self.transport.disconnect()

    def run_forever(self) -> None:
        """Block the main thread until interrupted."""
        try:
            while self._running:
                time.sleep(1)
                self._tick()
        except KeyboardInterrupt:
            self.stop()

    # ── Abstract methods for subclasses ────────────────

    @abstractmethod
    def _subscribe_topics(self) -> None:
        """Subscribe to role-specific MQTT topics."""

    @abstractmethod
    def _handle_message(self, topic: str, envelope: MessageEnvelope) -> None:
        """Handle a role-specific message."""

    def _on_start(self) -> None:
        """Called after agent is fully started. Override for setup."""

    def _on_stop(self) -> None:
        """Called before disconnect. Override for cleanup."""

    def _tick(self) -> None:
        """Called every second in the main loop. Override for periodic work."""

    # ── Discovery ──────────────────────────────────────

    def _announce(self) -> None:
        """Publish discovery announcement (retained)."""
        announce = DiscoveryAnnounce(
            agent_id=self.agent_id,
            role=self.role,
            capabilities=self.capabilities,
            goods_categories=self.capabilities,
            public_key_hex=self.identity.public_key_hex,
            status="online",
        )
        envelope = build_envelope(self.agent_id, self.role, announce, self.hlc)
        self.transport.publish(DISCOVERY_ANNOUNCE, envelope, retain=True)

    def _heartbeat_loop(self) -> None:
        """Periodic heartbeat publisher."""
        while self._running:
            try:
                hb = Heartbeat(
                    agent_id=self.agent_id,
                    role=self.role,
                    status="healthy" if self.state_machine.is_operational else "degraded",
                    load=min(1.0, self._active_orders / max(1, 5)),
                    active_orders=self._active_orders,
                    uptime_seconds=time.time() - self._start_time,
                )
                envelope = build_envelope(self.agent_id, self.role, hb, self.hlc)
                self.transport.publish(DISCOVERY_HEARTBEAT, envelope, qos=0)
            except Exception:
                logger.exception("[%s] Heartbeat error", self.agent_id)
            time.sleep(self.config.heartbeat_interval)

    def _liveness_loop(self) -> None:
        """Periodic check for dead peers."""
        while self._running:
            try:
                changed = self.registry.check_liveness(self.config.heartbeat_interval)
                for agent_id, new_state in changed:
                    logger.warning(
                        "[%s] Peer %s is now %s", self.agent_id, agent_id, new_state.value
                    )
                    self._on_peer_state_change(agent_id, new_state)
            except Exception:
                logger.exception("[%s] Liveness check error", self.agent_id)
            time.sleep(self.config.heartbeat_interval)

    def _on_peer_state_change(self, peer_id: str, new_state: AgentState) -> None:
        """Called when a peer's liveness state changes. Override for self-healing."""

    # ── Message dispatch ───────────────────────────────

    def _dispatch_envelope(self, topic: str, envelope: MessageEnvelope) -> None:
        """Route incoming messages to appropriate handlers."""
        sender = envelope.header.sender_id
        if sender == self.agent_id:
            return  # Skip own messages

        # Verify signature
        if not verify_envelope(envelope):
            logger.warning("[%s] Invalid signature from %s on %s", self.agent_id, sender, topic)
            return

        # Update HLC from remote timestamp
        if envelope.header.hlc:
            self.hlc.receive(envelope.header.hlc)

        # Handle discovery messages
        if topic == DISCOVERY_ANNOUNCE:
            self._handle_announce(envelope)
        elif topic == DISCOVERY_HEARTBEAT:
            self._handle_heartbeat(envelope)
        elif topic == DISCOVERY_GOODBYE:
            self._handle_goodbye(envelope)
        else:
            # Delegate to subclass
            self._handle_message(topic, envelope)

    def _handle_announce(self, envelope: MessageEnvelope) -> None:
        p = envelope.payload
        peer = self.registry.update_from_announce(
            agent_id=p["agent_id"],
            role=p["role"],
            capabilities=p.get("capabilities", []),
            goods_categories=p.get("goods_categories", []),
            public_key_hex=p.get("public_key_hex", ""),
            status=p.get("status", "online"),
        )
        # Register in reputation engine
        self.reputation.register(p["agent_id"], p["role"], p.get("capabilities", []))
        logger.info("[%s] Discovered peer: %s (%s)", self.agent_id, p["agent_id"], p["role"])

    def _handle_heartbeat(self, envelope: MessageEnvelope) -> None:
        p = envelope.payload
        self.registry.update_from_heartbeat(
            agent_id=p["agent_id"],
            role=p.get("role", ""),
            status=p.get("status", "healthy"),
            load=p.get("load", 0.0),
            active_orders=p.get("active_orders", 0),
        )

    def _handle_goodbye(self, envelope: MessageEnvelope) -> None:
        p = envelope.payload
        self.registry.mark_goodbye(p["agent_id"])
        logger.info("[%s] Peer %s said goodbye", self.agent_id, p["agent_id"])

    # ── Helpers ────────────────────────────────────────

    def publish(
        self, topic: str, payload, qos: int | None = None, retain: bool = False
    ) -> None:
        """Build an envelope and publish to a topic."""
        envelope = build_envelope(self.agent_id, self.role, payload, self.hlc)
        self.transport.publish(topic, envelope, qos=qos, retain=retain)

    @property
    def uptime(self) -> float:
        return time.time() - self._start_time
