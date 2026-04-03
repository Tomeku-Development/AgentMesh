"""Track active WebSocket agent sessions per workspace."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mesh_platform.gateway.agent_session import AgentSession

logger = logging.getLogger(__name__)

# workspace_id -> { agent_mesh_id -> AgentSession }
_connections: dict[str, dict[str, "AgentSession"]] = {}


def connect(workspace_id: str, agent_mesh_id: str, session: "AgentSession") -> None:
    ws_map = _connections.setdefault(workspace_id, {})
    ws_map[agent_mesh_id] = session
    logger.info("Gateway: agent %s connected to workspace %s (%d total)", agent_mesh_id, workspace_id, len(ws_map))


def disconnect(workspace_id: str, agent_mesh_id: str) -> None:
    ws_map = _connections.get(workspace_id)
    if ws_map:
        ws_map.pop(agent_mesh_id, None)
        if not ws_map:
            _connections.pop(workspace_id, None)
        logger.info("Gateway: agent %s disconnected from workspace %s", agent_mesh_id, workspace_id)


def count(workspace_id: str) -> int:
    return len(_connections.get(workspace_id, {}))


def get_all(workspace_id: str) -> list["AgentSession"]:
    return list(_connections.get(workspace_id, {}).values())


def clear_all() -> None:
    """For testing: reset all connections."""
    _connections.clear()
