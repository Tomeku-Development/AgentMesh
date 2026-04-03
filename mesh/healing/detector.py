"""Heartbeat-based failure detection for mesh peers."""

from __future__ import annotations

import logging
import time

from mesh.core.messages import HealthAlert
from mesh.core.registry import PeerRegistry
from mesh.core.state import AgentState

logger = logging.getLogger(__name__)


class FailureDetector:
    """Monitors peer heartbeats and detects failures.

    Runs on every agent. Failure is confirmed when multiple agents
    independently detect the same peer as DEAD and publish alerts.
    """

    def __init__(
        self,
        my_agent_id: str,
        registry: PeerRegistry,
        heartbeat_interval: float = 5.0,
    ) -> None:
        self._my_id = my_agent_id
        self._registry = registry
        self._heartbeat_interval = heartbeat_interval
        self._confirmed_dead: set[str] = set()
        self._death_votes: dict[str, set[str]] = {}  # agent_id -> set of voters

    def check(self) -> list[HealthAlert]:
        """Run a liveness check cycle. Returns new alerts to publish."""
        changed = self._registry.check_liveness(self._heartbeat_interval)
        alerts = []

        for agent_id, new_state in changed:
            peer = self._registry.get(agent_id)
            if not peer:
                continue

            if new_state == AgentState.SUSPECT:
                alert = HealthAlert(
                    detector_id=self._my_id,
                    suspect_agent_id=agent_id,
                    alert_type="heartbeat_timeout",
                    severity="warning",
                    missed_heartbeats=peer.missed_heartbeats,
                    last_seen_seconds_ago=time.time() - peer.last_seen,
                    recommended_action="monitor",
                )
                alerts.append(alert)

            elif new_state == AgentState.DEAD:
                if agent_id not in self._confirmed_dead:
                    alert = HealthAlert(
                        detector_id=self._my_id,
                        suspect_agent_id=agent_id,
                        alert_type="heartbeat_timeout",
                        severity="critical",
                        missed_heartbeats=peer.missed_heartbeats,
                        last_seen_seconds_ago=time.time() - peer.last_seen,
                        recommended_action="redistribute",
                    )
                    alerts.append(alert)
                    # Vote for death
                    self._death_votes.setdefault(agent_id, set()).add(self._my_id)

        return alerts

    def process_health_alert(self, alert: HealthAlert) -> bool:
        """Process a health alert from another agent.

        Returns True if quorum reached (>= 2 agents agree peer is dead).
        """
        if alert.severity == "critical":
            self._death_votes.setdefault(alert.suspect_agent_id, set()).add(alert.detector_id)
            votes = len(self._death_votes[alert.suspect_agent_id])
            if votes >= 2 and alert.suspect_agent_id not in self._confirmed_dead:
                self._confirmed_dead.add(alert.suspect_agent_id)
                logger.warning(
                    "Death confirmed for %s (votes: %d)",
                    alert.suspect_agent_id, votes,
                )
                return True
        return False

    def is_confirmed_dead(self, agent_id: str) -> bool:
        return agent_id in self._confirmed_dead

    def agent_recovered(self, agent_id: str) -> None:
        """Clear death status when an agent comes back."""
        self._confirmed_dead.discard(agent_id)
        self._death_votes.pop(agent_id, None)
