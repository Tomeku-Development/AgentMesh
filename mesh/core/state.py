"""Agent finite state machine for lifecycle management."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone


class AgentState(str, enum.Enum):
    """Possible states for an agent in the mesh."""
    IDLE = "idle"            # Just started, not yet discovered peers
    ACTIVE = "active"        # Normal operation
    BUSY = "busy"            # At max concurrent orders
    DEGRADED = "degraded"    # Experiencing issues but functional
    SUSPECT = "suspect"      # Missed heartbeats (peer view)
    DEAD = "dead"            # Confirmed failure (peer view)
    REJOINING = "rejoining"  # Coming back online after failure
    SHUTDOWN = "shutdown"    # Graceful shutdown


# Valid state transitions
_TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.IDLE: {AgentState.ACTIVE, AgentState.SHUTDOWN},
    AgentState.ACTIVE: {AgentState.BUSY, AgentState.DEGRADED, AgentState.SHUTDOWN},
    AgentState.BUSY: {AgentState.ACTIVE, AgentState.DEGRADED, AgentState.SHUTDOWN},
    AgentState.DEGRADED: {AgentState.ACTIVE, AgentState.SHUTDOWN},
    AgentState.SUSPECT: {AgentState.DEAD, AgentState.ACTIVE},
    AgentState.DEAD: {AgentState.REJOINING},
    AgentState.REJOINING: {AgentState.ACTIVE, AgentState.DEGRADED},
    AgentState.SHUTDOWN: set(),
}


@dataclass
class StateMachine:
    """Tracks an agent's state with transition validation and history."""

    current: AgentState = AgentState.IDLE
    history: list[tuple[str, AgentState, AgentState]] = field(default_factory=list)

    def transition(self, new_state: AgentState) -> bool:
        """Attempt a state transition. Returns True if valid and applied."""
        if new_state == self.current:
            return True
        valid_targets = _TRANSITIONS.get(self.current, set())
        if new_state not in valid_targets:
            return False
        old = self.current
        self.current = new_state
        ts = datetime.now(timezone.utc).isoformat()
        self.history.append((ts, old, new_state))
        return True

    def can_transition(self, new_state: AgentState) -> bool:
        """Check if a transition is valid without applying it."""
        if new_state == self.current:
            return True
        return new_state in _TRANSITIONS.get(self.current, set())

    @property
    def is_operational(self) -> bool:
        """True if the agent can accept work."""
        return self.current in {AgentState.ACTIVE, AgentState.BUSY, AgentState.REJOINING}
