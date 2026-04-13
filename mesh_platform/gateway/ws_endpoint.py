"""FastAPI WebSocket endpoint for SDK agent connections."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

import mesh_platform.models.base as _base_mod
from mesh_platform.gateway import connection_manager
from mesh_platform.gateway.agent_session import AgentSession
from mesh_platform.gateway.protocol import WSRegisterMessage, WSSystemMessage, parse_client_message
from mesh.core.capability_utils import validate_capabilities
from mesh_platform.services.capability_seed import CAPABILITY_SEEDS
from mesh_platform.config import settings
from mesh_platform.services.api_key_service import validate_api_key

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level override for testing (set to a callable to skip real MQTT)
_transport_factory = None


@router.websocket("/ws/v1/agent")
async def agent_websocket(
    websocket: WebSocket,
    api_key: str = Query(default=""),
):
    """WebSocket gateway for SDK agent connections."""
    if not api_key:
        await websocket.close(code=4001, reason="Missing api_key")
        return

    async with _base_mod.async_session_factory() as db:
        result = await validate_api_key(db, api_key)
        if result is None:
            await websocket.accept()
            await websocket.send_text(
                WSSystemMessage(event="error", data={"detail": "Invalid or expired API key"}).model_dump_json()
            )
            await websocket.close(code=4001, reason="Invalid API key")
            return
        key_obj, user, workspace = result
        await db.commit()

    current_count = connection_manager.count(workspace.id)
    max_conns = getattr(settings, "gateway_max_connections_per_workspace", 50)
    if current_count >= max_conns:
        await websocket.accept()
        await websocket.send_text(
            WSSystemMessage(event="error", data={"detail": "Workspace connection limit reached"}).model_dump_json()
        )
        await websocket.close(code=4029, reason="Connection limit reached")
        return

    await websocket.accept()

    try:
        raw = await websocket.receive_text()
        data = json.loads(raw)
        msg = parse_client_message(data)
        if not isinstance(msg, WSRegisterMessage):
            await websocket.send_text(
                WSSystemMessage(event="error", data={"detail": "First message must be 'register'"}).model_dump_json()
            )
            await websocket.close(code=4002, reason="Expected register message")
            return
    except (json.JSONDecodeError, ValueError, WebSocketDisconnect) as e:
        logger.warning("Register failed: %s", e)
        return

    session = AgentSession(
        websocket=websocket,
        workspace_id=workspace.id,
        workspace_slug=workspace.slug,
        user_id=user.id,
        agent_id=msg.agent_id,
        agent_role=msg.role,
        capabilities=msg.capabilities,
        transport_factory=_transport_factory,
    )

    # Validate and log unknown capabilities
    known_caps = {cap["name"] for cap in CAPABILITY_SEEDS}
    _, unknown_caps = validate_capabilities(msg.capabilities, known_caps)
    if unknown_caps:
        logger.warning(
            "Agent %s registered with unknown capabilities: %s",
            session.agent_id, unknown_caps,
        )

    connection_manager.connect(workspace.id, session.agent_id, session)

    try:
        await session.start()
        while True:
            raw = await websocket.receive_text()
            await session.handle_message(raw)
    except WebSocketDisconnect:
        logger.info("SDK agent %s disconnected", session.agent_id)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
    finally:
        await session.teardown()
        connection_manager.disconnect(workspace.id, session.agent_id)
