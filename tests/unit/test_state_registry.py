"""Tests for HLC, state machine, registry, and failure detector."""

import time
import pytest
from mesh.core.clock import HLC
from mesh.core.state import StateMachine, AgentState
from mesh.core.registry import PeerRegistry
from mesh.healing.detector import FailureDetector
from mesh.healing.redistributor import RoleRedistributor
from mesh.healing.recovery import RecoveryManager


class TestHLC:
    def test_tick_advances(self):
        hlc = HLC.create("node1")
        ts1 = hlc.tick()
        ts2 = hlc.tick()
        parsed1 = HLC.parse(ts1)
        parsed2 = HLC.parse(ts2)
        assert parsed2 >= parsed1

    def test_receive_merges(self):
        hlc1 = HLC.create("node1")
        hlc2 = HLC.create("node2")
        ts1 = hlc1.tick()
        ts2 = hlc2.receive(ts1)
        parsed = HLC.parse(ts2)
        assert parsed.node_id == "node2"

    def test_parse_format_roundtrip(self):
        hlc = HLC.create("test-node")
        ts = hlc.tick()
        parsed = HLC.parse(ts)
        assert parsed.node_id == "test-node"
        assert parsed.format() == ts

    def test_ordering(self):
        a = HLC(physical=100, logical=0, node_id="a")
        b = HLC(physical=100, logical=1, node_id="a")
        c = HLC(physical=101, logical=0, node_id="a")
        assert a < b
        assert b < c


class TestStateMachine:
    def test_initial_state_is_idle(self):
        sm = StateMachine()
        assert sm.current == AgentState.IDLE

    def test_valid_transition(self):
        sm = StateMachine()
        assert sm.transition(AgentState.ACTIVE)
        assert sm.current == AgentState.ACTIVE

    def test_invalid_transition_rejected(self):
        sm = StateMachine()
        assert not sm.transition(AgentState.DEAD)  # Can't go IDLE -> DEAD
        assert sm.current == AgentState.IDLE

    def test_transition_history(self):
        sm = StateMachine()
        sm.transition(AgentState.ACTIVE)
        sm.transition(AgentState.BUSY)
        assert len(sm.history) == 2

    def test_is_operational(self):
        sm = StateMachine()
        assert not sm.is_operational
        sm.transition(AgentState.ACTIVE)
        assert sm.is_operational

    def test_same_state_transition_ok(self):
        sm = StateMachine()
        sm.transition(AgentState.ACTIVE)
        assert sm.transition(AgentState.ACTIVE)  # No-op, returns True


class TestPeerRegistry:
    def test_update_from_announce(self, registry):
        peer = registry.update_from_announce("agent-1", "buyer", ["electronics"])
        assert peer.agent_id == "agent-1"
        assert peer.role == "buyer"
        assert len(registry) == 1

    def test_update_from_heartbeat(self, registry):
        registry.update_from_announce("agent-1", "buyer")
        peer = registry.update_from_heartbeat("agent-1", load=0.5, active_orders=2)
        assert peer.load == 0.5
        assert peer.active_orders == 2

    def test_heartbeat_unknown_peer_returns_none(self, registry):
        assert registry.update_from_heartbeat("unknown") is None

    def test_get_by_role(self, registry):
        registry.update_from_announce("s1", "supplier", ["electronics"])
        registry.update_from_announce("s2", "supplier", ["batteries"])
        registry.update_from_announce("b1", "buyer")
        suppliers = registry.get_by_role("supplier")
        assert len(suppliers) == 2

    def test_get_by_capability(self, registry):
        registry.update_from_announce("s1", "supplier", ["electronics", "displays"])
        registry.update_from_announce("s2", "supplier", ["electronics", "batteries"])
        display_agents = registry.get_by_capability("displays")
        assert len(display_agents) == 1

    def test_mark_goodbye(self, registry):
        registry.update_from_announce("agent-1", "buyer")
        registry.mark_goodbye("agent-1")
        peer = registry.get("agent-1")
        assert peer.state == AgentState.SHUTDOWN

    def test_check_liveness_marks_suspect(self, registry):
        registry.update_from_announce("agent-1", "buyer")
        peer = registry.get("agent-1")
        peer.last_seen = time.time() - 20  # 20s ago (> 15s suspect threshold)
        changed = registry.check_liveness()
        assert len(changed) == 1
        assert changed[0] == ("agent-1", AgentState.SUSPECT)

    def test_longest_uptime_peer(self, registry):
        registry.update_from_announce("old", "buyer")
        old_peer = registry.get("old")
        old_peer.first_seen = time.time() - 100

        registry.update_from_announce("new", "supplier")
        senior = registry.longest_uptime_peer
        assert senior.agent_id == "old"


class TestFailureDetector:
    def test_detect_suspect(self, registry):
        registry.update_from_announce("agent-1", "buyer")
        registry.get("agent-1").last_seen = time.time() - 20
        detector = FailureDetector("detector-1", registry)
        alerts = detector.check()
        assert any(a.severity == "warning" for a in alerts)

    def test_detect_dead(self, registry):
        registry.update_from_announce("agent-1", "buyer")
        registry.get("agent-1").last_seen = time.time() - 35
        detector = FailureDetector("detector-1", registry)
        alerts = detector.check()
        assert any(a.severity == "critical" for a in alerts)

    def test_quorum_confirmation(self, registry):
        registry.update_from_announce("target", "supplier")
        detector = FailureDetector("det-1", registry)
        from mesh.core.messages import HealthAlert
        alert1 = HealthAlert(
            detector_id="det-1", suspect_agent_id="target",
            alert_type="heartbeat_timeout", severity="critical",
        )
        alert2 = HealthAlert(
            detector_id="det-2", suspect_agent_id="target",
            alert_type="heartbeat_timeout", severity="critical",
        )
        assert not detector.process_health_alert(alert1)  # 1 vote, not enough
        assert detector.process_health_alert(alert2)  # 2 votes, confirmed


class TestRoleRedistributor:
    def test_same_role_replacement(self, registry):
        registry.update_from_announce("s1", "supplier", ["electronics"])
        registry.update_from_announce("s2", "supplier", ["electronics"])
        registry.get("s2").state = AgentState.DEAD

        redistributor = RoleRedistributor("coordinator", registry)
        result = redistributor.compute_redistribution("s2")
        assert result is not None
        assert result.replacement_agent_id == "s1"

    def test_no_replacement_returns_none(self, registry):
        registry.update_from_announce("s1", "supplier", ["electronics"])
        registry.get("s1").state = AgentState.DEAD

        redistributor = RoleRedistributor("coordinator", registry)
        result = redistributor.compute_redistribution("s1")
        assert result is None


class TestRecoveryManager:
    def test_recovery_tracking(self, registry):
        registry.update_from_announce("agent-1", "buyer")
        mgr = RecoveryManager("coordinator", registry)
        mgr.start_recovery("agent-1", recovery_epochs=2)
        assert mgr.is_recovering("agent-1")
        assert mgr.max_load_for("agent-1") == 0.5

    def test_recovery_completes(self, registry):
        registry.update_from_announce("agent-1", "buyer")
        mgr = RecoveryManager("coordinator", registry)
        mgr.start_recovery("agent-1", recovery_epochs=1)
        completed = mgr.tick_epoch()
        assert "agent-1" in completed
        assert not mgr.is_recovering("agent-1")
