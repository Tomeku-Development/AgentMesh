"""State recovery for agents rejoining the mesh."""

from __future__ import annotations

import asyncio
import logging

from mesh.core.registry import PeerRegistry
from mesh.core.state import AgentState
from mesh.llm.router import LLMDisabledError, LLMProviderError, LLMRouter

logger = logging.getLogger(__name__)


class RecoveryManager:
    """Manages the recovery process when a previously-dead agent comes back.

    Recovery steps:
    1. Agent re-announces with status "rejoining"
    2. Syncs reputation scores from retained MQTT messages
    3. Syncs ledger balances from retained MQTT messages
    4. Operates at 50% capacity for 2 epochs before full activation
    """

    def __init__(
        self,
        my_agent_id: str,
        registry: PeerRegistry,
        llm_router: LLMRouter | None = None,
    ) -> None:
        self._my_id = my_agent_id
        self._registry = registry
        self._llm_router = llm_router
        self._recovering_agents: dict[str, int] = {}  # agent_id -> epochs remaining

    def start_recovery(self, agent_id: str, recovery_epochs: int = 2) -> None:
        """Begin recovery process for a rejoining agent."""
        # Try LLM for optimal recovery parameters
        max_load_factor = 0.5  # Default

        if self._llm_router is not None:
            try:
                peer = self._registry.get(agent_id)
                peer_role = peer.role if peer else "unknown"

                # Build a simple prompt for recovery parameters
                system_prompt = """You are a recovery advisor for the MESH supply chain network.
Your role is to recommend optimal recovery parameters for agents rejoining after a failure.

Respond with a JSON object:
{
    "recovery_epochs": int (1-10),
    "max_load_factor": float (0.1-0.9),
    "reasoning": "brief explanation"
}

Consider:
- Critical roles need faster recovery
- More complex roles may need longer recovery
- Lower load factor means safer but slower recovery"""

                user_prompt = f"""Determine recovery parameters for a rejoining agent.

## Agent Information
- Agent ID: {agent_id[:8]}
- Role: {peer_role}
- Recovery status: Rejoining after failure

## Recovery Guidelines
- Default recovery epochs: {recovery_epochs}
- Default max load factor: 0.5

Recommend optimal recovery parameters."""

                result = asyncio.run(
                    self._llm_router.complete_json(user_prompt, system_prompt)
                )

                # Validate LLM values
                llm_epochs = result.get("recovery_epochs", recovery_epochs)
                llm_load_factor = result.get("max_load_factor", max_load_factor)

                if 1 <= llm_epochs <= 10:
                    recovery_epochs = llm_epochs
                if 0.1 <= llm_load_factor <= 0.9:
                    max_load_factor = llm_load_factor

                logger.info(
                    "LLM recovery params for %s: epochs=%d, load_factor=%.2f, reasoning=%s",
                    agent_id[:8], recovery_epochs, max_load_factor,
                    result.get("reasoning", "N/A")[:50],
                )

            except (LLMDisabledError, LLMProviderError, Exception) as e:
                logger.warning("LLM recovery params failed, using defaults: %s", e)

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
