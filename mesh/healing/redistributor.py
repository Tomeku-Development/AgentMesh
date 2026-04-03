"""Role redistribution when agents fail."""

from __future__ import annotations

import logging

from mesh.core.messages import RoleRedistribution
from mesh.core.registry import PeerInfo, PeerRegistry
from mesh.core.state import AgentState

logger = logging.getLogger(__name__)


class RoleRedistributor:
    """Coordinates role reassignment when an agent is confirmed dead.

    The longest-uptime active agent acts as coordinator to avoid
    multiple agents issuing conflicting redistributions. Since all agents
    see the same BFT-ordered messages, they all agree on who coordinates.
    """

    def __init__(self, my_agent_id: str, registry: PeerRegistry) -> None:
        self._my_id = my_agent_id
        self._registry = registry
        self._redistributions: list[RoleRedistribution] = []

    def am_i_coordinator(self) -> bool:
        """Check if this agent should coordinate redistribution."""
        senior = self._registry.longest_uptime_peer
        return senior is not None and senior.agent_id == self._my_id

    def compute_redistribution(
        self,
        failed_agent_id: str,
        active_orders: list[str] | None = None,
    ) -> RoleRedistribution | None:
        """Compute role redistribution for a failed agent.

        Strategy:
        1. If another agent of the same role exists, it absorbs the workload.
        2. If not, find the agent with closest capability match and lowest load.
        3. If no suitable replacement, return None (degraded mode).
        """
        failed_peer = self._registry.get(failed_agent_id)
        if not failed_peer:
            return None

        failed_role = failed_peer.role
        failed_caps = failed_peer.capabilities

        # Strategy 1: Same-role agent
        same_role = [
            p for p in self._registry.get_by_role(failed_role)
            if p.agent_id != failed_agent_id
        ]
        if same_role:
            # Pick the one with lowest load
            replacement = min(same_role, key=lambda p: p.load)
            redistribution = RoleRedistribution(
                failed_agent_id=failed_agent_id,
                failed_role=failed_role,
                replacement_agent_id=replacement.agent_id,
                assumed_capabilities=failed_caps,
                active_orders_transferred=active_orders or [],
            )
            self._redistributions.append(redistribution)
            logger.info(
                "Redistributing %s's role to same-role peer %s",
                failed_agent_id[:8], replacement.agent_id[:8],
            )
            return redistribution

        # Strategy 2: Closest capability match
        active = self._registry.active_peers()
        best_match: PeerInfo | None = None
        best_overlap = -1

        for peer in active:
            if peer.agent_id == failed_agent_id:
                continue
            overlap = len(set(peer.capabilities) & set(failed_caps))
            if overlap > best_overlap or (overlap == best_overlap and peer.load < (best_match.load if best_match else 1.0)):
                best_match = peer
                best_overlap = overlap

        if best_match and best_overlap > 0:
            redistribution = RoleRedistribution(
                failed_agent_id=failed_agent_id,
                failed_role=failed_role,
                replacement_agent_id=best_match.agent_id,
                assumed_capabilities=list(set(best_match.capabilities) & set(failed_caps)),
                active_orders_transferred=active_orders or [],
            )
            self._redistributions.append(redistribution)
            logger.info(
                "Redistributing %s's role to capability-matched peer %s (overlap: %d)",
                failed_agent_id[:8], best_match.agent_id[:8], best_overlap,
            )
            return redistribution

        logger.warning("No suitable replacement for %s — entering degraded mode", failed_agent_id[:8])
        return None
