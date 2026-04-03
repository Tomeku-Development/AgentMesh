"""Integration tests for peer discovery and registry synchronization."""

import time
import pytest
from mesh.core.identity import AgentIdentity
from mesh.core.registry import PeerRegistry
from mesh.core.state import AgentState
from mesh.core.messages import DiscoveryAnnounce, Heartbeat, Goodbye
from mesh.core.protocol import build_envelope, verify_envelope
from mesh.core.clock import HLC


class TestDiscoveryLifecycle:
    """Test the full discovery → heartbeat → goodbye lifecycle."""

    @pytest.fixture
    def registry(self):
        return PeerRegistry(suspect_threshold=2.0, dead_threshold=4.0)

    @pytest.fixture
    def agents(self):
        return [
            {"id": f"agent_{i:03d}", "role": role, "caps": caps}
            for i, (role, caps) in enumerate([
                ("buyer", ["electronics"]),
                ("supplier", ["electronics", "displays"]),
                ("supplier", ["electronics", "batteries"]),
                ("logistics", ["shipping"]),
                ("inspector", ["quality_control"]),
            ])
        ]

    def test_announce_registers_all_peers(self, registry, agents):
        for agent in agents:
            registry.update_from_announce(
                agent_id=agent["id"],
                role=agent["role"],
                capabilities=agent["caps"],
                goods_categories=agent["caps"],
                public_key_hex="abcd1234",
                status="online",
            )
        assert len(registry.active_peers()) == 5

    def test_heartbeat_updates_peer_state(self, registry, agents):
        # First announce
        registry.update_from_announce(
            agent_id="agent_000", role="buyer", capabilities=["electronics"],
            goods_categories=["electronics"], public_key_hex="abcd", status="online",
        )
        # Then heartbeat
        peer = registry.update_from_heartbeat(
            agent_id="agent_000", role="buyer", status="healthy", load=0.3, active_orders=2,
        )
        assert peer is not None
        assert peer.load == 0.3
        assert peer.active_orders == 2

    def test_goodbye_removes_peer(self, registry, agents):
        registry.update_from_announce(
            agent_id="agent_000", role="buyer", capabilities=["electronics"],
            goods_categories=["electronics"], public_key_hex="abcd", status="online",
        )
        registry.mark_goodbye("agent_000")
        assert len(registry.active_peers()) == 0

    def test_liveness_detects_missing_heartbeat(self, registry):
        registry.update_from_announce(
            agent_id="agent_000", role="buyer", capabilities=[],
            goods_categories=[], public_key_hex="", status="online",
        )
        # Force last_seen far in the past
        peer = registry._peers["agent_000"]
        peer.last_seen = time.time() - 3.0  # > suspect_threshold (2.0)
        changed = registry.check_liveness(1.0)
        assert any(aid == "agent_000" and state == AgentState.SUSPECT for aid, state in changed)

    def test_dead_after_prolonged_absence(self, registry):
        registry.update_from_announce(
            agent_id="agent_000", role="buyer", capabilities=[],
            goods_categories=[], public_key_hex="", status="online",
        )
        peer = registry._peers["agent_000"]
        peer.last_seen = time.time() - 5.0  # > dead_threshold (4.0)
        changed = registry.check_liveness(1.0)
        assert any(aid == "agent_000" and state == AgentState.DEAD for aid, state in changed)

    def test_get_by_role_filters_correctly(self, registry, agents):
        for agent in agents:
            registry.update_from_announce(
                agent_id=agent["id"], role=agent["role"], capabilities=agent["caps"],
                goods_categories=agent["caps"], public_key_hex="", status="online",
            )
        suppliers = registry.get_by_role("supplier")
        assert len(suppliers) == 2
        assert all(p.role == "supplier" for p in suppliers)

    def test_get_by_capability_finds_matching(self, registry, agents):
        for agent in agents:
            registry.update_from_announce(
                agent_id=agent["id"], role=agent["role"], capabilities=agent["caps"],
                goods_categories=agent["caps"], public_key_hex="", status="online",
            )
        electronics_agents = registry.get_by_capability("electronics")
        # buyer, supplier_0, supplier_1, inspector all have "electronics"
        assert len(electronics_agents) >= 3


class TestEnvelopeIntegrity:
    """Test message envelope signing/verification end-to-end."""

    def test_envelope_roundtrip_with_announce(self):
        hlc = HLC.create("node1")
        announce = DiscoveryAnnounce(
            agent_id="test_agent",
            role="buyer",
            capabilities=["electronics"],
            goods_categories=["electronics"],
            public_key_hex="deadbeef",
            status="online",
        )
        envelope = build_envelope("test_agent", "buyer", announce, hlc)
        assert verify_envelope(envelope)
        assert envelope.payload["agent_id"] == "test_agent"

    def test_envelope_roundtrip_with_heartbeat(self):
        hlc = HLC.create("node2")
        hb = Heartbeat(
            agent_id="test_agent",
            role="supplier",
            status="healthy",
            load=0.5,
            active_orders=3,
            uptime_seconds=120.0,
        )
        envelope = build_envelope("test_agent", "supplier", hb, hlc)
        assert verify_envelope(envelope)
        assert envelope.payload["load"] == 0.5

    def test_hlc_causality_across_agents(self):
        hlc_a = HLC.create("agent_a")
        hlc_b = HLC.create("agent_b")
        # Agent A ticks
        ts_a1 = hlc_a.tick()
        # Agent B receives A's message
        ts_b1 = hlc_b.receive(ts_a1)
        # B's clock should be >= A's
        parts_a = ts_a1.split(":")
        parts_b = ts_b1.split(":")
        assert int(parts_b[0]) >= int(parts_a[0])

    def test_multiple_identities_sign_independently(self):
        id_a = AgentIdentity.generate()
        id_b = AgentIdentity.generate()
        msg = b"test message"
        sig_a = id_a.sign(msg)
        sig_b = id_b.sign(msg)
        assert sig_a != sig_b
        assert id_a.verify(msg, sig_a)
        assert id_b.verify(msg, sig_b)
        assert not id_a.verify(msg, sig_b)  # Cross-verify fails
