"""WebSocket protocol message types for the SDK gateway."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, field_validator


# ── Client → Server ──────────────────────────────────────────────────────

class WSRegisterMessage(BaseModel):
    type: Literal["register"] = "register"
    role: str
    capabilities: list[str] = []
    balance: float = 10000.0
    agent_id: str | None = None

    @field_validator("capabilities", mode="before")
    @classmethod
    def _normalize_capabilities(cls, v: list[str]) -> list[str]:
        """Normalize capabilities: lowercase, strip, replace spaces/hyphens with underscores."""
        from mesh.core.capability_utils import normalize_capabilities
        if isinstance(v, list):
            return normalize_capabilities(v)
        return []


class WSSubscribeMessage(BaseModel):
    type: Literal["subscribe"] = "subscribe"
    topics: list[str]


class WSUnsubscribeMessage(BaseModel):
    type: Literal["unsubscribe"] = "unsubscribe"
    topics: list[str]


class WSPublishMessage(BaseModel):
    type: Literal["publish"] = "publish"
    topic: str
    payload: dict[str, Any]


class WSPingMessage(BaseModel):
    type: Literal["ping"] = "ping"


# ── Server → Client ──────────────────────────────────────────────────────

class WSSystemMessage(BaseModel):
    type: Literal["system"] = "system"
    event: str
    data: dict[str, Any] = {}


class WSMessageMessage(BaseModel):
    type: Literal["message"] = "message"
    topic: str
    payload: dict[str, Any]
    header: dict[str, Any] = {}


class WSPongMessage(BaseModel):
    type: Literal["pong"] = "pong"


class WSAckMessage(BaseModel):
    type: Literal["ack"] = "ack"
    ref: str


# ── Parsing ──────────────────────────────────────────────────────────────

_CLIENT_MSG_MAP = {
    "register": WSRegisterMessage,
    "subscribe": WSSubscribeMessage,
    "unsubscribe": WSUnsubscribeMessage,
    "publish": WSPublishMessage,
    "ping": WSPingMessage,
}


def parse_client_message(
    data: dict[str, Any],
) -> WSRegisterMessage | WSSubscribeMessage | WSUnsubscribeMessage | WSPublishMessage | WSPingMessage:
    """Parse a raw dict from the WebSocket into a typed message."""
    msg_type = data.get("type")
    cls = _CLIENT_MSG_MAP.get(msg_type)  # type: ignore[arg-type]
    if cls is None:
        raise ValueError(f"Unknown message type: {msg_type}")
    return cls.model_validate(data)
