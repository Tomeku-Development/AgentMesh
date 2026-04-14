"""Platform configuration via environment variables (PLATFORM_ prefix)."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class PlatformSettings(BaseSettings):
    model_config = {"env_prefix": "PLATFORM_"}

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://mesh:mesh@localhost:5432/mesh_platform"

    @property
    def async_database_url(self) -> str:
        """Ensure the database URL uses the asyncpg driver.

        Railway and other providers give postgresql:// URLs, but
        SQLAlchemy async requires postgresql+asyncpg://.
        """
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # Auth / JWT
    secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # MQTT (for sink + agent manager)
    mqtt_host: str = "127.0.0.1"
    mqtt_port: int = 1883

    # Xendit
    xendit_secret_key: str = ""
    xendit_webhook_token: str = ""

    # Cryptomus
    cryptomus_merchant_id: str = ""
    cryptomus_api_key: str = ""

    # Defaults
    default_max_agents: int = 10
    default_plan: str = "starter"

    # Gateway
    gateway_max_connections_per_workspace: int = 50
    gateway_heartbeat_interval: float = 5.0
    gateway_hmac_secret: str = "mesh-vertex-swarm-2026"


settings = PlatformSettings()
