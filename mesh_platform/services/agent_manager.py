"""Agent lifecycle manager: start/stop tenant agent processes."""

from __future__ import annotations

import logging
import multiprocessing
from typing import Any

logger = logging.getLogger(__name__)

# Track running agent processes: key = (workspace_id, agent_definition_id)
_running_agents: dict[tuple[str, str], multiprocessing.Process] = {}


def _agent_worker(
    agent_role: str,
    tenant_slug: str,
    mesh_config_dict: dict[str, Any],
    agent_kwargs: dict[str, Any],
) -> None:
    """Worker function that runs in a subprocess."""
    from mesh.core.config import MeshConfig

    config = MeshConfig(**mesh_config_dict)

    # Dynamic import based on role
    role_map = {
        "buyer": "mesh.agents.buyer.BuyerAgent",
        "supplier": "mesh.agents.supplier.SupplierAgent",
        "logistics": "mesh.agents.logistics.LogisticsAgent",
        "inspector": "mesh.agents.inspector.InspectorAgent",
        "oracle": "mesh.agents.oracle.OracleAgent",
    }

    agent_path = role_map.get(agent_role)
    if not agent_path:
        logger.error("Unknown agent role: %s", agent_role)
        return

    module_path, class_name = agent_path.rsplit(".", 1)
    import importlib

    module = importlib.import_module(module_path)
    agent_class = getattr(module, class_name)

    # Use TenantBaseAgent mixin pattern would require more refactoring.
    # For now, we modify the config to use tenant-prefixed topics via env.
    agent = agent_class(config=config, **agent_kwargs)
    agent.run()


def start_agent(
    workspace_id: str,
    agent_definition_id: str,
    agent_role: str,
    tenant_slug: str,
    mesh_config_dict: dict[str, Any],
    agent_kwargs: dict[str, Any] | None = None,
) -> bool:
    """Spawn an agent process for a workspace."""
    key = (workspace_id, agent_definition_id)
    if key in _running_agents and _running_agents[key].is_alive():
        logger.warning("Agent %s already running", key)
        return False

    proc = multiprocessing.Process(
        target=_agent_worker,
        args=(agent_role, tenant_slug, mesh_config_dict, agent_kwargs or {}),
        daemon=True,
    )
    proc.start()
    _running_agents[key] = proc
    logger.info("Started agent %s (pid=%d)", key, proc.pid)
    return True


def stop_agent(workspace_id: str, agent_definition_id: str) -> bool:
    """Stop a running agent process."""
    key = (workspace_id, agent_definition_id)
    proc = _running_agents.pop(key, None)
    if proc is None or not proc.is_alive():
        return False
    proc.terminate()
    proc.join(timeout=5)
    if proc.is_alive():
        proc.kill()
    logger.info("Stopped agent %s", key)
    return True


def list_running() -> list[dict]:
    """Return info about all running agents."""
    result = []
    for (ws_id, agent_id), proc in _running_agents.items():
        result.append({
            "workspace_id": ws_id,
            "agent_definition_id": agent_id,
            "pid": proc.pid,
            "alive": proc.is_alive(),
        })
    return result
