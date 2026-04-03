"""Message envelope construction, signing, and verification."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from mesh.core.clock import HLC
from mesh.core.crypto import canonical_json, sign_message, verify_signature
from mesh.core.messages import MessageEnvelope, MessageHeader


def build_envelope(
    sender_id: str,
    sender_role: str,
    payload: BaseModel | dict[str, Any],
    hlc: HLC | None = None,
    secret: bytes = b"mesh-vertex-swarm-2026",
) -> MessageEnvelope:
    """Construct a signed message envelope.

    Args:
        sender_id: Agent's 16-char hex ID.
        sender_role: One of buyer/supplier/logistics/inspector/oracle.
        payload: Pydantic model or dict for the message payload.
        hlc: Hybrid logical clock (will be ticked).
        secret: HMAC secret for signing.

    Returns:
        A signed MessageEnvelope ready to publish.
    """
    hlc_str = hlc.tick() if hlc else ""

    header = MessageHeader(
        sender_id=sender_id,
        sender_role=sender_role,
        hlc=hlc_str,
    )

    if isinstance(payload, BaseModel):
        payload_dict = payload.model_dump()
    else:
        payload_dict = payload

    # Sign header + payload
    signable = {"header": header.model_dump(), "payload": payload_dict}
    signature = sign_message(signable, secret)

    return MessageEnvelope(
        header=header,
        payload=payload_dict,
        signature=signature,
    )


def verify_envelope(
    envelope: MessageEnvelope,
    secret: bytes = b"mesh-vertex-swarm-2026",
) -> bool:
    """Verify the HMAC signature of a message envelope."""
    signable = {"header": envelope.header.model_dump(), "payload": envelope.payload}
    return verify_signature(signable, envelope.signature, secret)


def serialize_envelope(envelope: MessageEnvelope) -> str:
    """Serialize an envelope to JSON string for MQTT publishing."""
    return envelope.model_dump_json()


def deserialize_envelope(data: str | bytes) -> MessageEnvelope:
    """Deserialize an MQTT message payload into a MessageEnvelope."""
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    return MessageEnvelope.model_validate_json(data)
