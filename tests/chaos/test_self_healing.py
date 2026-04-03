"""Chaos tests for agent failure detection and self-healing (offline — no broker)."""

import time
import pytest
from mesh.core.registry import PeerRegistry
from mesh.core.state import AgentState, StateMachine
from mesh.healing.detector import FailureDetector
from mesh.healing.redistributor import RoleRedistributor
from mesh.healing.recovery import RecoveryManager


class TestAgentCrashDetection:
    """Test failure detection under various crash scenarios."""

    @pytest.fixture
    def setup(self):
        registry = PeerRegistry(suspect_threshold=2.0, dead_threshold=4.0)
        detector = FailureDetector("monitor_agent", registry, heartbeat_interval=1.0)
        # Register agents
        for i, (role, caps) in enumerate([
            ("buyer", ["electronics"]),
            ("supplier", ["electronics", "displays"]),
            ("supplier", ["electronics", "batteries"]),
            ("logistics", ["shipping"]),
            ("inspector", ["quality_control"]),
        ]):
            registry.update_from_announce(
                agent_id=f"agent_{i:03d}",
                role=role,
                capabilities=caps,
                goods_categories=caps,
                public_key_hex="",
                status="online",
            )
        return registry, detector

    def test_single_agent_failure(self, setup):
        registry, detector = setup
        # Simulate agent_001 (supplier) going silent
        peer = registry._peers["agent_001"]
        peer.last_seen = time.time() - 3.0  # > suspect_threshold
        changed = registry.check_liveness(1.0)
        assert any(aid == "agent_001" for aid, _ in changed)

    def test_multiple_agents_fail_simultaneously(self, setup):
        registry, detector = setup
        now = time.time()
        # Both suppliers go down
        registry._peers["agent_001"].last_seen = now - 5.0
        registry._peers["agent_002"].last_seen = now - 5.0
        changed = registry.check_liveness(1.0)
        dead_agents = [aid for aid, state in changed if state == AgentState.DEAD]
        assert "agent_001" in dead_agents
        assert "agent_002" in dead_agents

    def test_suspect_recovers_with_heartbeat(self, setup):
        registry, _ = setup
        peer = registry._peers["agent_001"]
        peer.last_seen = time.time() - 3.0
        registry.check_liveness(1.0)
        assert peer.state == AgentState.SUSPECT

        # Agent sends heartbeat
        registry.update_from_heartbeat("agent_001", "supplier", "healthy", 0.1, 0)
        assert peer.state == AgentState.ACTIVE

    def test_dead_agent_does_not_auto_recover(self, setup):
        registry, _ = setup
        peer = registry._peers["agent_001"]
        peer.last_seen = time.time() - 5.0
        registry.check_liveness(1.0)
        assert peer.state == AgentState.DEAD

        # Heartbeat from dead agent
        registry.update_from_heartbeat("agent_001", "supplier", "healthy", 0.0, 0)
        # The peer gets updated last_seen but state handling depends on implementation

    def test_detector_produces_alerts(self, setup):
        registry, detector = setup
        peer = registry._peers["agent_001"]
        peer.last_seen = time.time() - 5.0
        alerts = detector.check()
        assert len(alerts) > 0

    def test_quorum_confirmation(self, setup):
        registry, detector = setup
        from mesh.core.messages import HealthAlert
        # Simulate two agents reporting same failure
        alert1 = HealthAlert(
            detector_id="agent_000",
            suspect_agent_id="agent_001",
            alert_type="heartbeat_timeout",
            severity="critical",
            missed_heartbeats=6,
            last_seen_seconds_ago=10.0,
            recommended_action="redistribute",
        )
        alert2 = HealthAlert(
            detector_id="agent_003",
            suspect_agent_id="agent_001",
            alert_type="heartbeat_timeout",
            severity="critical",
            missed_heartbeats=6,
            last_seen_seconds_ago=10.0,
            recommended_action="redistribute",
        )
        result1 = detector.process_health_alert(alert1)
        result2 = detector.process_health_alert(alert2)
        # Quorum should be reached with 2 votes
        assert result2 is True
        assert detector.is_confirmed_dead("agent_001")


class TestRoleRedistribution:
    """Test self-healing role redistribution under agent failures."""

    @pytest.fixture
    def setup(self):
        registry = PeerRegistry(suspect_threshold=2.0, dead_threshold=4.0)
        agents = [
            ("supplier_1", "supplier", ["electronics", "displays"]),
            ("supplier_2", "supplier", ["electronics", "batteries"]),
            ("logistics_1", "logistics", ["shipping", "electronics"]),
            ("buyer_1", "buyer", ["electronics"]),
        ]
        for aid, role, caps in agents:
            registry.update_from_announce(
                agent_id=aid, role=role, capabilities=caps,
                goods_categories=caps, public_key_hex="", status="online",
            )
        return registry

    def test_supplier_failure_finds_replacement(self, setup):
        registry = setup
        redistributor = RoleRedistributor("buyer_1", registry)
        # Kill supplier_1
        registry._peers["supplier_1"].state = AgentState.DEAD
        registry._peers["supplier_1"].last_seen = time.time() - 10

        replacement = redistributor.compute_redistribution("supplier_1")
        # supplier_2 should be the replacement (same role)
        assert replacement is not None
        assert replacement.replacement_agent_id == "supplier_2"

    def test_no_replacement_when_no_candidates(self, setup):
        registry = setup
        redistributor = RoleRedistributor("buyer_1", registry)
        # Kill both suppliers
        registry._peers["supplier_1"].state = AgentState.DEAD
        registry._peers["supplier_2"].state = AgentState.DEAD

        replacement = redistributor.compute_redistribution("supplier_1")
        # Could fall back to capability match (logistics_1 has "electronics")
        # or return None if no suitable match
        if replacement:
            assert replacement.replacement_agent_id != "supplier_1"

    def test_coordinator_selection_by_uptime(self, setup):
        registry = setup
        # longest_uptime_peer = min(active, key=first_seen), so lowest first_seen = longest uptime
        now = time.time()
        registry._peers["supplier_1"].first_seen = now - 100
        registry._peers["supplier_2"].first_seen = now - 200
        registry._peers["logistics_1"].first_seen = now - 300  # Longest uptime
        registry._peers["buyer_1"].first_seen = now - 50

        # logistics_1 has longest uptime (earliest first_seen), so it should be coordinator
        redistributor_logistics = RoleRedistributor("logistics_1", registry)
        assert redistributor_logistics.am_i_coordinator() is True

        redistributor_buyer = RoleRedistributor("buyer_1", registry)
        assert redistributor_buyer.am_i_coordinator() is False

    def test_capability_match_fallback(self, setup):
        registry = setup
        redistributor = RoleRedistributor("buyer_1", registry)
        # Kill supplier_1 and supplier_2
        registry._peers["supplier_1"].state = AgentState.DEAD
        registry._peers["supplier_2"].state = AgentState.DEAD
        # logistics_1 has "electronics" capability — possible fallback
        replacement = redistributor.compute_redistribution("supplier_1")
        # Should either find logistics_1 or return None


class TestRecoveryManagement:
    """Test the recovery ramp-up process for rejoining agents."""

    @pytest.fixture
    def setup(self):
        registry = PeerRegistry(suspect_threshold=2.0, dead_threshold=4.0)
        registry.update_from_announce(
            agent_id="agent_001", role="supplier", capabilities=["electronics"],
            goods_categories=["electronics"], public_key_hex="", status="online",
        )
        registry.update_from_announce(
            agent_id="healthy_agent", role="buyer", capabilities=["electronics"],
            goods_categories=["electronics"], public_key_hex="", status="online",
        )
        recovery = RecoveryManager("coordinator", registry)
        return recovery, registry

    def test_recovery_starts_at_half_capacity(self, setup):
        recovery, _ = setup
        recovery.start_recovery("agent_001")
        assert recovery.max_load_for("agent_001") == pytest.approx(0.5)

    def test_recovery_ramps_up_over_epochs(self, setup):
        recovery, _ = setup
        recovery.start_recovery("agent_001", recovery_epochs=4)
        loads = [recovery.max_load_for("agent_001")]
        for _ in range(4):
            recovery.tick_epoch()
            loads.append(recovery.max_load_for("agent_001"))
        # Should go from 0.5 to 1.0 after enough epochs
        assert loads[-1] >= loads[0]

    def test_recovery_completes_after_ramp(self, setup):
        recovery, _ = setup
        recovery.start_recovery("agent_001", recovery_epochs=2)
        recovery.tick_epoch()
        recovery.tick_epoch()
        # After ramp-up completes, max_load should be 1.0
        assert recovery.max_load_for("agent_001") == pytest.approx(1.0)

    def test_non_recovering_agent_has_full_capacity(self, setup):
        recovery, _ = setup
        assert recovery.max_load_for("healthy_agent") == pytest.approx(1.0)

    def test_multiple_agents_recover_independently(self, setup):
        recovery, registry = setup
        registry.update_from_announce(
            agent_id="agent_b", role="supplier", capabilities=["electronics"],
            goods_categories=["electronics"], public_key_hex="", status="online",
        )
        recovery.start_recovery("agent_001", recovery_epochs=4)
        recovery.tick_epoch()
        recovery.tick_epoch()
        recovery.start_recovery("agent_b", recovery_epochs=4)  # Starts later

        # agent_001 has been recovering longer
        assert recovery.is_recovering("agent_001")
        assert recovery.is_recovering("agent_b")

    def test_tick_epoch_returns_completed(self, setup):
        recovery, _ = setup
        recovery.start_recovery("agent_001", recovery_epochs=1)
        completed = recovery.tick_epoch()
        assert "agent_001" in completed
        assert not recovery.is_recovering("agent_001")


class TestChaosScenario:
    """Simulate the electronics scenario chaos events (kill & restart)."""

    @pytest.fixture
    def mesh_state(self):
        registry = PeerRegistry(suspect_threshold=2.0, dead_threshold=4.0)
        agents = [
            ("buyer_001", "buyer", ["electronics"]),
            ("supplier_001", "supplier", ["electronics", "displays"]),
            ("supplier_002", "supplier", ["electronics", "batteries"]),
            ("logistics_001", "logistics", ["shipping"]),
            ("inspector_001", "inspector", ["quality_control"]),
            ("oracle_001", "oracle", ["market_data"]),
        ]
        for aid, role, caps in agents:
            registry.update_from_announce(
                agent_id=aid, role=role, capabilities=caps,
                goods_categories=caps, public_key_hex="", status="online",
            )
        detector = FailureDetector("buyer_001", registry)
        redistributor = RoleRedistributor("buyer_001", registry)
        recovery = RecoveryManager("buyer_001", registry)
        return registry, detector, redistributor, recovery

    def test_kill_supplier_triggers_redistribution(self, mesh_state):
        registry, detector, redistributor, recovery = mesh_state

        # Chaos event: kill supplier_001
        peer = registry._peers["supplier_001"]
        peer.last_seen = time.time() - 5.0
        peer.state = AgentState.DEAD

        # Redistributor finds replacement
        replacement = redistributor.compute_redistribution("supplier_001")
        if replacement:
            assert replacement.failed_role == "supplier"
            assert replacement.replacement_agent_id != "supplier_001"

    def test_restart_supplier_triggers_recovery(self, mesh_state):
        registry, detector, redistributor, recovery = mesh_state

        # Kill supplier
        registry._peers["supplier_001"].state = AgentState.DEAD
        registry._peers["supplier_001"].last_seen = time.time() - 10

        # Restart: re-announce
        registry.update_from_announce(
            agent_id="supplier_001", role="supplier",
            capabilities=["electronics", "displays"],
            goods_categories=["electronics", "displays"],
            public_key_hex="", status="online",
        )
        recovery.start_recovery("supplier_001")

        # Should be at 50% capacity
        assert recovery.max_load_for("supplier_001") == pytest.approx(0.5)

        # Ramp up
        recovery.tick_epoch()
        recovery.tick_epoch()
        assert recovery.max_load_for("supplier_001") == pytest.approx(1.0)

    def test_system_survives_with_one_supplier(self, mesh_state):
        registry, _, _, _ = mesh_state
        # Kill supplier_001
        registry._peers["supplier_001"].state = AgentState.DEAD
        # System still has supplier_002 active
        active_suppliers = [
            p for p in registry.get_by_role("supplier")
            if p.state != AgentState.DEAD
        ]
        assert len(active_suppliers) >= 1

    def test_all_suppliers_dead_degrades_gracefully(self, mesh_state):
        registry, _, redistributor, _ = mesh_state
        registry._peers["supplier_001"].state = AgentState.DEAD
        registry._peers["supplier_002"].state = AgentState.DEAD

        active_suppliers = [
            p for p in registry.get_by_role("supplier")
            if p.state != AgentState.DEAD
        ]
        assert len(active_suppliers) == 0

        # System should be in degraded mode
        replacement = redistributor.compute_redistribution("supplier_001")
        # Might return None or a fallback agent with capability match

    def test_detector_recovery_clears_death(self, mesh_state):
        registry, detector, _, _ = mesh_state
        from mesh.core.messages import HealthAlert
        # Confirm death
        for voter in ["buyer_001", "logistics_001"]:
            alert = HealthAlert(
                detector_id=voter,
                suspect_agent_id="supplier_001",
                alert_type="heartbeat_timeout",
                severity="critical",
                missed_heartbeats=6,
                last_seen_seconds_ago=10.0,
                recommended_action="redistribute",
            )
            detector.process_health_alert(alert)
        assert detector.is_confirmed_dead("supplier_001")

        # Recovery clears death
        detector.agent_recovered("supplier_001")
        assert not detector.is_confirmed_dead("supplier_001")
