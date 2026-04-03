"""Peer discovery registry — tracks known agents in the mesh."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Iterator

from mesh.core.state import AgentState


@dataclass
class PeerInfo:
    """Information about a discovered peer agent."""
    agent_id: str
    role: str
    capabilities: list[str] = field(default_factory=list)
    goods_categories: list[str] = field(default_factory=list)
    public_key_hex: str = ""
    status: str = "online"
    state: AgentState = AgentState.ACTIVE
    last_seen: float = field(default_factory=time.time)
    first_seen: float = field(default_factory=time.time)
    load: float = 0.0
    active_orders: int = 0
    missed_heartbeats: int = 0


class PeerRegistry:
    """Maintains a local view of all known peers in the mesh."""

    def __init__(self, suspect_threshold: float = 15.0, dead_threshold: float = 30.0) -> None:
        self._peers: dict[str, PeerInfo] = {}
        self._suspect_threshold = suspect_threshold
        self._dead_threshold = dead_threshold

    def update_from_announce(
        self,
        agent_id: str,
        role: str,
        capabilities: list[str] | None = None,
        goods_categories: list[str] | None = None,
        public_key_hex: str = "",
        status: str = "online",
    ) -> PeerInfo:
        """Update or create a peer from a discovery announcement."""
        now = time.time()
        if agent_id in self._peers:
            peer = self._peers[agent_id]
            peer.role = role
            peer.capabilities = capabilities or peer.capabilities
            peer.goods_categories = goods_categories or peer.goods_categories
            peer.public_key_hex = public_key_hex or peer.public_key_hex
            peer.status = status
            peer.last_seen = now
            peer.missed_heartbeats = 0
            if status == "rejoining":
                peer.state = AgentState.REJOINING
            elif peer.state in {AgentState.SUSPECT, AgentState.DEAD}:
                peer.state = AgentState.ACTIVE
        else:
            peer = PeerInfo(
                agent_id=agent_id,
                role=role,
                capabilities=capabilities or [],
                goods_categories=goods_categories or [],
                public_key_hex=public_key_hex,
                status=status,
                first_seen=now,
                last_seen=now,
            )
            self._peers[agent_id] = peer
        return peer

    def update_from_heartbeat(
        self,
        agent_id: str,
        role: str = "",
        status: str = "healthy",
        load: float = 0.0,
        active_orders: int = 0,
    ) -> PeerInfo | None:
        """Update peer from a heartbeat. Returns None if peer unknown."""
        if agent_id not in self._peers:
            return None
        peer = self._peers[agent_id]
        peer.last_seen = time.time()
        peer.missed_heartbeats = 0
        peer.load = load
        peer.active_orders = active_orders
        if status == "healthy" and peer.state in {AgentState.SUSPECT, AgentState.DEAD}:
            peer.state = AgentState.ACTIVE
        peer.status = status
        return peer

    def mark_goodbye(self, agent_id: str) -> None:
        """Mark a peer as shutdown."""
        if agent_id in self._peers:
            self._peers[agent_id].state = AgentState.SHUTDOWN

    def remove(self, agent_id: str) -> None:
        """Remove a peer entirely."""
        self._peers.pop(agent_id, None)

    def check_liveness(self, heartbeat_interval: float = 5.0) -> list[tuple[str, AgentState]]:
        """Check all peers for liveness. Returns list of (agent_id, new_state) for changed peers."""
        now = time.time()
        changed: list[tuple[str, AgentState]] = []
        for peer in self._peers.values():
            if peer.state in {AgentState.SHUTDOWN, AgentState.DEAD}:
                continue
            age = now - peer.last_seen
            if age >= self._dead_threshold and peer.state != AgentState.DEAD:
                peer.state = AgentState.DEAD
                changed.append((peer.agent_id, AgentState.DEAD))
            elif age >= self._suspect_threshold and peer.state != AgentState.SUSPECT:
                peer.state = AgentState.SUSPECT
                peer.missed_heartbeats = int(age / heartbeat_interval)
                changed.append((peer.agent_id, AgentState.SUSPECT))
        return changed

    def get(self, agent_id: str) -> PeerInfo | None:
        return self._peers.get(agent_id)

    def get_by_role(self, role: str) -> list[PeerInfo]:
        """Get all active peers with a given role."""
        return [
            p for p in self._peers.values()
            if p.role == role and p.state in {AgentState.ACTIVE, AgentState.BUSY, AgentState.REJOINING}
        ]

    def get_by_capability(self, capability: str) -> list[PeerInfo]:
        """Get all active peers with a given capability."""
        return [
            p for p in self._peers.values()
            if capability in p.capabilities
            and p.state in {AgentState.ACTIVE, AgentState.BUSY, AgentState.REJOINING}
        ]

    def active_peers(self) -> list[PeerInfo]:
        """All peers that are operational."""
        return [
            p for p in self._peers.values()
            if p.state in {AgentState.ACTIVE, AgentState.BUSY, AgentState.REJOINING}
        ]

    def all_peers(self) -> list[PeerInfo]:
        return list(self._peers.values())

    def __len__(self) -> int:
        return len(self._peers)

    def __iter__(self) -> Iterator[PeerInfo]:
        return iter(self._peers.values())

    @property
    def longest_uptime_peer(self) -> PeerInfo | None:
        """Return the active peer with the longest uptime (for coordination)."""
        active = self.active_peers()
        if not active:
            return None
        return min(active, key=lambda p: p.first_seen)
