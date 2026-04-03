"""Configuration management using Pydantic Settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class MeshConfig(BaseSettings):
    """MESH agent configuration loaded from environment variables."""

    model_config = {"env_prefix": "MESH_"}

    # Broker connection
    broker_host: str = "127.0.0.1"
    broker_port: int = 1883
    broker_username: str = ""
    broker_password: str = ""

    # Agent identity
    agent_role: str = "buyer"
    agent_id: str = "auto"  # "auto" = derive from Ed25519 pubkey
    capabilities: str = ""  # comma-separated

    # Economics
    initial_balance: float = 10000.0
    min_balance: float = 50.0

    # Timing (seconds)
    heartbeat_interval: float = 5.0
    suspect_threshold: float = 15.0  # 3 missed heartbeats
    dead_threshold: float = 30.0  # 6 missed heartbeats
    bid_window: float = 10.0
    negotiate_window: float = 15.0
    negotiate_max_rounds: int = 3
    execute_timeout: float = 30.0
    verify_timeout: float = 10.0
    settle_timeout: float = 5.0

    # Reputation
    reputation_initial: float = 0.5
    reputation_decay_factor: float = 0.98
    epoch_duration: float = 60.0

    # Scenario
    scenario: str = "electronics"
    log_level: str = "INFO"

    def get_capabilities(self) -> list[str]:
        """Parse comma-separated capabilities into list."""
        if not self.capabilities:
            return []
        return [c.strip() for c in self.capabilities.split(",") if c.strip()]
