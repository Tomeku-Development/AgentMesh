"""Tests for SLA monitoring service — rule CRUD, metric computation, evaluation, and alerts."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.models.agent import AgentDefinition, AgentStatusLog
from mesh_platform.models.order import Order, OrderEvent
from mesh_platform.models.sla import SLAAlert, SLARule
from mesh_platform.models.user import User
from mesh_platform.models.workspace import Workspace, WorkspaceMembership
from mesh_platform.schemas.sla import MetricType, Operator, SLARuleCreate
from mesh_platform.services import sla_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def workspace(db_session: AsyncSession) -> Workspace:
    """Create a test workspace with an owner user."""
    user = User(
        id=str(uuid.uuid4()),
        email="sla-owner@mesh.io",
        display_name="SLA Owner",
        password_hash="hashed",
    )
    db_session.add(user)
    ws = Workspace(
        id=str(uuid.uuid4()),
        name="SLA Test Workspace",
        slug="sla-test",
        owner_id=user.id,
    )
    db_session.add(ws)
    membership = WorkspaceMembership(
        id=str(uuid.uuid4()),
        workspace_id=ws.id,
        user_id=user.id,
        role="owner",
    )
    db_session.add(membership)
    await db_session.flush()
    return ws


# ---------------------------------------------------------------------------
# Rule CRUD tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_rule(db_session: AsyncSession, workspace: Workspace):
    """Creating an SLA rule persists it with correct fields."""
    data = SLARuleCreate(
        metric_type=MetricType.order_settlement_time,
        threshold=120.0,
        operator=Operator.greater_than,
        check_interval_seconds=300,
    )
    rule = await sla_service.create_rule(db_session, workspace.id, data)

    assert rule.id is not None
    assert rule.workspace_id == workspace.id
    assert rule.metric_type == "order_settlement_time"
    assert rule.threshold == 120.0
    assert rule.operator == "greater_than"
    assert rule.check_interval_seconds == 300
    assert rule.is_active is True


@pytest.mark.asyncio
async def test_list_rules(db_session: AsyncSession, workspace: Workspace):
    """Listing rules returns all rules for the workspace."""
    for metric in [MetricType.order_settlement_time, MetricType.agent_uptime]:
        data = SLARuleCreate(
            metric_type=metric,
            threshold=50.0,
            operator=Operator.less_than,
            check_interval_seconds=600,
        )
        await sla_service.create_rule(db_session, workspace.id, data)

    rules = await sla_service.list_rules(db_session, workspace.id)
    assert len(rules) == 2


@pytest.mark.asyncio
async def test_delete_rule(db_session: AsyncSession, workspace: Workspace):
    """Deleting a rule removes it; deleting a non-existent rule returns False."""
    data = SLARuleCreate(
        metric_type=MetricType.order_success_rate,
        threshold=90.0,
        operator=Operator.less_than,
        check_interval_seconds=300,
    )
    rule = await sla_service.create_rule(db_session, workspace.id, data)

    assert await sla_service.delete_rule(db_session, rule.id) is True
    assert await sla_service.delete_rule(db_session, "nonexistent-id") is False

    rules = await sla_service.list_rules(db_session, workspace.id)
    assert len(rules) == 0


# ---------------------------------------------------------------------------
# Metric computation tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_order_settlement_time_no_data(db_session: AsyncSession, workspace: Workspace):
    """Returns 0.0 when no order events exist (division-by-zero safe)."""
    result = await sla_service.compute_order_settlement_time(db_session, workspace.id, 300)
    assert result == 0.0


@pytest.mark.asyncio
async def test_order_settlement_time_with_data(db_session: AsyncSession, workspace: Workspace):
    """Computes average settlement time from request to settled events."""
    now = datetime.now(timezone.utc)
    order_id = str(uuid.uuid4())

    # Create order
    order = Order(
        id=order_id,
        workspace_id=workspace.id,
        goods="Widget",
        quantity=10,
        max_price_per_unit=50.0,
        current_status="settled",
        created_at=now - timedelta(seconds=100),
    )
    db_session.add(order)

    # Request event at t-100s
    db_session.add(OrderEvent(
        order_id=order_id,
        workspace_id=workspace.id,
        event_type="request",
        agent_id="buyer01",
        occurred_at=now - timedelta(seconds=100),
    ))
    # Settled event at t-40s (60 seconds later)
    db_session.add(OrderEvent(
        order_id=order_id,
        workspace_id=workspace.id,
        event_type="settled",
        agent_id="buyer01",
        occurred_at=now - timedelta(seconds=40),
    ))
    await db_session.flush()

    result = await sla_service.compute_order_settlement_time(db_session, workspace.id, 300)
    # Should be approximately 60 seconds
    assert 59.0 <= result <= 61.0


@pytest.mark.asyncio
async def test_agent_uptime_no_data(db_session: AsyncSession, workspace: Workspace):
    """Returns 0.0 when no agent status logs exist (division-by-zero safe)."""
    result = await sla_service.compute_agent_uptime(db_session, workspace.id, 300)
    assert result == 0.0


@pytest.mark.asyncio
async def test_agent_uptime_with_data(db_session: AsyncSession, workspace: Workspace):
    """Computes percentage of active heartbeats."""
    now = datetime.now(timezone.utc)
    agent_def = AgentDefinition(
        id=str(uuid.uuid4()),
        workspace_id=workspace.id,
        agent_role="buyer",
        agent_mesh_id="buyer01",
    )
    db_session.add(agent_def)

    # 3 active, 1 inactive = 75% uptime
    for i, status in enumerate(["active", "active", "active", "inactive"]):
        db_session.add(AgentStatusLog(
            agent_definition_id=agent_def.id,
            workspace_id=workspace.id,
            status=status,
            recorded_at=now - timedelta(seconds=i * 10),
        ))
    await db_session.flush()

    result = await sla_service.compute_agent_uptime(db_session, workspace.id, 300)
    assert result == 75.0


@pytest.mark.asyncio
async def test_order_success_rate_no_data(db_session: AsyncSession, workspace: Workspace):
    """Returns 0.0 when no orders exist (division-by-zero safe)."""
    result = await sla_service.compute_order_success_rate(db_session, workspace.id, 300)
    assert result == 0.0


@pytest.mark.asyncio
async def test_order_success_rate_with_data(db_session: AsyncSession, workspace: Workspace):
    """Computes percentage of settled orders out of total orders."""
    now = datetime.now(timezone.utc)

    # Create 4 orders, 3 settled
    for i in range(4):
        oid = str(uuid.uuid4())
        order = Order(
            id=oid,
            workspace_id=workspace.id,
            goods="Widget",
            quantity=10,
            max_price_per_unit=50.0,
            current_status="settled" if i < 3 else "requested",
            created_at=now - timedelta(seconds=50),
        )
        db_session.add(order)
        if i < 3:
            db_session.add(OrderEvent(
                order_id=oid,
                workspace_id=workspace.id,
                event_type="settled",
                agent_id="buyer01",
                occurred_at=now - timedelta(seconds=30),
            ))
    await db_session.flush()

    result = await sla_service.compute_order_success_rate(db_session, workspace.id, 300)
    assert result == 75.0


# ---------------------------------------------------------------------------
# Evaluation tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_rules_creates_alert_on_breach(
    db_session: AsyncSession, workspace: Workspace
):
    """Evaluation creates an alert when a metric breaches the threshold."""
    now = datetime.now(timezone.utc)

    # Create an order with settlement time ~60s
    oid = str(uuid.uuid4())
    db_session.add(Order(
        id=oid, workspace_id=workspace.id, goods="Widget",
        quantity=10, max_price_per_unit=50.0, current_status="settled",
        created_at=now - timedelta(seconds=100),
    ))
    db_session.add(OrderEvent(
        order_id=oid, workspace_id=workspace.id, event_type="request",
        agent_id="buyer01", occurred_at=now - timedelta(seconds=100),
    ))
    db_session.add(OrderEvent(
        order_id=oid, workspace_id=workspace.id, event_type="settled",
        agent_id="buyer01", occurred_at=now - timedelta(seconds=40),
    ))
    await db_session.flush()

    # Rule: settlement time > 30s should breach
    rule_data = SLARuleCreate(
        metric_type=MetricType.order_settlement_time,
        threshold=30.0,
        operator=Operator.greater_than,
        check_interval_seconds=300,
    )
    await sla_service.create_rule(db_session, workspace.id, rule_data)

    alerts = await sla_service.evaluate_rules(db_session, workspace.id)
    assert len(alerts) == 1
    assert alerts[0].metric_type == "order_settlement_time"
    assert alerts[0].actual_value > 30.0
    assert alerts[0].threshold_value == 30.0
    assert alerts[0].acknowledged is False


@pytest.mark.asyncio
async def test_evaluate_rules_no_breach(db_session: AsyncSession, workspace: Workspace):
    """Evaluation creates no alerts when metrics are within thresholds."""
    now = datetime.now(timezone.utc)

    # Create an order with settlement time ~60s
    oid = str(uuid.uuid4())
    db_session.add(Order(
        id=oid, workspace_id=workspace.id, goods="Widget",
        quantity=10, max_price_per_unit=50.0, current_status="settled",
        created_at=now - timedelta(seconds=100),
    ))
    db_session.add(OrderEvent(
        order_id=oid, workspace_id=workspace.id, event_type="request",
        agent_id="buyer01", occurred_at=now - timedelta(seconds=100),
    ))
    db_session.add(OrderEvent(
        order_id=oid, workspace_id=workspace.id, event_type="settled",
        agent_id="buyer01", occurred_at=now - timedelta(seconds=40),
    ))
    await db_session.flush()

    # Rule: settlement time > 120s — should NOT breach (actual ~60s)
    rule_data = SLARuleCreate(
        metric_type=MetricType.order_settlement_time,
        threshold=120.0,
        operator=Operator.greater_than,
        check_interval_seconds=300,
    )
    await sla_service.create_rule(db_session, workspace.id, rule_data)

    alerts = await sla_service.evaluate_rules(db_session, workspace.id)
    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_evaluate_rules_less_than_breach(
    db_session: AsyncSession, workspace: Workspace
):
    """Evaluation detects breach with less_than operator."""
    now = datetime.now(timezone.utc)

    # Create agent status logs: 1 active, 3 inactive = 25% uptime
    agent_def = AgentDefinition(
        id=str(uuid.uuid4()),
        workspace_id=workspace.id,
        agent_role="buyer",
        agent_mesh_id="buyer02",
    )
    db_session.add(agent_def)
    for i, status in enumerate(["active", "inactive", "inactive", "inactive"]):
        db_session.add(AgentStatusLog(
            agent_definition_id=agent_def.id,
            workspace_id=workspace.id,
            status=status,
            recorded_at=now - timedelta(seconds=i * 10),
        ))
    await db_session.flush()

    # Rule: uptime < 50% should breach (actual is 25%)
    rule_data = SLARuleCreate(
        metric_type=MetricType.agent_uptime,
        threshold=50.0,
        operator=Operator.less_than,
        check_interval_seconds=300,
    )
    await sla_service.create_rule(db_session, workspace.id, rule_data)

    alerts = await sla_service.evaluate_rules(db_session, workspace.id)
    assert len(alerts) == 1
    assert alerts[0].metric_type == "agent_uptime"
    assert alerts[0].actual_value == 25.0


# ---------------------------------------------------------------------------
# Alert management tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_alerts_unacknowledged(db_session: AsyncSession, workspace: Workspace):
    """Lists only unacknowledged alerts ordered by breached_at DESC."""
    now = datetime.now(timezone.utc)

    # Create a rule to reference
    rule = SLARule(
        id=str(uuid.uuid4()),
        workspace_id=workspace.id,
        metric_type="order_settlement_time",
        threshold=30.0,
        operator="greater_than",
        check_interval_seconds=300,
        is_active=True,
    )
    db_session.add(rule)

    # Create 2 unacknowledged and 1 acknowledged alert
    for i in range(3):
        alert = SLAAlert(
            id=str(uuid.uuid4()),
            workspace_id=workspace.id,
            rule_id=rule.id,
            metric_type="order_settlement_time",
            actual_value=60.0 + i,
            threshold_value=30.0,
            breached_at=now - timedelta(minutes=i),
            acknowledged=i == 2,  # third alert is acknowledged
        )
        db_session.add(alert)
    await db_session.flush()

    alerts = await sla_service.list_alerts(db_session, workspace.id, unacknowledged_only=True)
    assert len(alerts) == 2
    # Should be ordered by breached_at DESC (most recent first)
    assert alerts[0].breached_at >= alerts[1].breached_at


@pytest.mark.asyncio
async def test_acknowledge_alert(db_session: AsyncSession, workspace: Workspace):
    """Acknowledging an alert sets acknowledged fields."""
    rule = SLARule(
        id=str(uuid.uuid4()),
        workspace_id=workspace.id,
        metric_type="agent_uptime",
        threshold=50.0,
        operator="less_than",
        check_interval_seconds=300,
        is_active=True,
    )
    db_session.add(rule)

    alert = SLAAlert(
        id=str(uuid.uuid4()),
        workspace_id=workspace.id,
        rule_id=rule.id,
        metric_type="agent_uptime",
        actual_value=25.0,
        threshold_value=50.0,
        breached_at=datetime.now(timezone.utc),
        acknowledged=False,
    )
    db_session.add(alert)
    await db_session.flush()

    user_id = "user-123"
    result = await sla_service.acknowledge_alert(db_session, alert.id, user_id)
    assert result is not None
    assert result.acknowledged is True
    assert result.acknowledged_by == user_id
    assert result.acknowledged_at is not None


@pytest.mark.asyncio
async def test_acknowledge_alert_not_found(db_session: AsyncSession, workspace: Workspace):
    """Acknowledging a non-existent alert returns None."""
    result = await sla_service.acknowledge_alert(db_session, "nonexistent-id", "user-123")
    assert result is None
