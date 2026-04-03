"""Hybrid Logical Clock for causal ordering across MQTT topics."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class HLC:
    """Hybrid Logical Clock combining physical time with logical counter.

    Provides causal ordering across agents even when wall clocks diverge.
    Format: "physical_ms:logical:node_id"
    """

    physical: int = 0  # milliseconds since epoch
    logical: int = 0
    node_id: str = ""

    @classmethod
    def create(cls, node_id: str) -> HLC:
        """Create a new HLC for a node, initialized to current time."""
        return cls(physical=_now_ms(), logical=0, node_id=node_id)

    def tick(self) -> str:
        """Advance the clock for a local event. Returns formatted timestamp."""
        now = _now_ms()
        if now > self.physical:
            self.physical = now
            self.logical = 0
        else:
            self.logical += 1
        return self.format()

    def receive(self, remote_str: str) -> str:
        """Update clock on receiving a remote event. Returns formatted timestamp."""
        remote = HLC.parse(remote_str)
        now = _now_ms()
        if now > self.physical and now > remote.physical:
            self.physical = now
            self.logical = 0
        elif self.physical == remote.physical:
            self.logical = max(self.logical, remote.logical) + 1
        elif self.physical > remote.physical:
            self.logical += 1
        else:
            self.physical = remote.physical
            self.logical = remote.logical + 1
        return self.format()

    def format(self) -> str:
        """Format as 'physical:logical:node_id'."""
        return f"{self.physical}:{self.logical}:{self.node_id}"

    @classmethod
    def parse(cls, hlc_str: str) -> HLC:
        """Parse an HLC string back into components."""
        parts = hlc_str.split(":")
        if len(parts) < 3:
            raise ValueError(f"Invalid HLC format: {hlc_str}")
        return cls(
            physical=int(parts[0]),
            logical=int(parts[1]),
            node_id=":".join(parts[2:]),  # node_id may contain colons
        )

    def __lt__(self, other: HLC) -> bool:
        if self.physical != other.physical:
            return self.physical < other.physical
        if self.logical != other.logical:
            return self.logical < other.logical
        return self.node_id < other.node_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HLC):
            return NotImplemented
        return (
            self.physical == other.physical
            and self.logical == other.logical
            and self.node_id == other.node_id
        )

    def __le__(self, other: HLC) -> bool:
        return self == other or self < other


def _now_ms() -> int:
    """Current time in milliseconds since epoch."""
    return int(time.time() * 1000)
