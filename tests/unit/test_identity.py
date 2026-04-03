"""Tests for Ed25519 identity management."""

import pytest
from mesh.core.identity import AgentIdentity


class TestAgentIdentity:
    def test_generate_creates_unique_ids(self):
        id1 = AgentIdentity.generate()
        id2 = AgentIdentity.generate()
        assert id1.agent_id != id2.agent_id
        assert id1.public_key_hex != id2.public_key_hex

    def test_agent_id_is_16_hex_chars(self):
        identity = AgentIdentity.generate()
        assert len(identity.agent_id) == 16
        int(identity.agent_id, 16)  # Should not raise

    def test_deterministic_from_seed(self):
        seed = b"\x00" * 32
        id1 = AgentIdentity.from_seed(seed)
        id2 = AgentIdentity.from_seed(seed)
        assert id1.agent_id == id2.agent_id
        assert id1.public_key_hex == id2.public_key_hex

    def test_from_hex_roundtrip(self):
        original = AgentIdentity.generate()
        seed_hex = original.seed_hex()
        restored = AgentIdentity.from_hex(seed_hex)
        assert original.agent_id == restored.agent_id

    def test_sign_and_verify(self):
        identity = AgentIdentity.generate()
        data = b"hello mesh"
        signature = identity.sign(data)
        assert identity.verify(data, signature)

    def test_verify_fails_on_tampered_data(self):
        identity = AgentIdentity.generate()
        data = b"hello mesh"
        signature = identity.sign(data)
        assert not identity.verify(b"tampered", signature)

    def test_verify_fails_with_wrong_key(self):
        id1 = AgentIdentity.generate()
        id2 = AgentIdentity.generate()
        data = b"hello mesh"
        signature = id1.sign(data)
        assert not id2.verify(data, signature)
