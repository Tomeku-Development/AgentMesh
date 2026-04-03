"""State recovery for agents rejoining the mesh."""

from __future__ import annotations

import logging

from mesh.core.registry import PeerRegistry
from mesh.core.state import AgentState

logger = logging.getLogger(__name__)


class RecoveryManager:
    """Manages the recovery process when a previously-dead agent comes back.

    Recovery steps:
    1. Agent re-announces with status "rejoining"
    2. Syncs reputation scores from retained MQTT messages
    3. Syncs ledger balances from retained MQTT messages
    4. Operates at 50% capacity for 2 epochs before full activation
    """

    def __init__(self, my_agent_id: str, registry: PeerRegistry) -> None:
        self._my_id = my_agent_id
        self._registry = registry
        self._recovering_agents: dict[str, int] = {}  # agent_id -> epochs remaining

    def start_recovery(self, agent_id: str, recovery_epochs: int = 2) -> None:
        """Begin recovery process for a rejoining agent."""
        self._recovering_agents[agent_id] = recovery_epochs
        peer = self._registry.get(agent_id)
        if peer:
            peer.state = AgentState.REJOINING
        logger.info("Started recovery for %s (%d epochs)", agent_id[:8], recovery_epochs)

    def tick_epoch(self) -> list[str]:
        """Advance recovery timers. Returns list of agents that completed recovery."""
        completed = []
        for agent_id in list(self._recovering_agents):
            self._recovering_agents[agent_id] -= 1
            if self._recovering_agents[agent_id] <= 0:
                del self._recovering_agents[agent_id]
                peer = self._registry.get(agent_id)
                if peer:
                    peer.state = AgentState.ACTIVE
                completed.append(agent_id)
                logger.info("Recovery complete for %s — now fully active", agent_id[:8])
        return completed

    def is_recovering(self, agent_id: str) -> bool:
        return agent_id in self._recovering_agents

    def max_load_for(self, agent_id: str) -> float:
        """Return max load factor for an agent (0.5 if recovering, 1.0 if normal)."""
        if agent_id in self._recovering_agents:
            return 0.5
        return 1.0
