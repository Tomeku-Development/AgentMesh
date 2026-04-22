"""Property-based tests for analytics aggregation correctness and order lifecycle duration.

**Feature: saas-platform-enhancements, Property 1: Analytics aggregation correctness**
**Validates: Requirements 1.1, 1.3**

**Feature: saas-platform-enhancements, Property 2: Order lifecycle duration computation**
**Validates: Requirements 1.2**
"""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from hypothesis import given, settings, strategies as st, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from mesh_platform.models.base import Base
from mesh_platform.models.user import User  # noqa: F401
from mesh_platform.models.workspace import Workspace, WorkspaceMembership  # noqa: F401
from mesh_platform.models.order import Order, OrderEvent  # noqa: F401
from mesh_platform.models.ledger import LedgerEntry, EscrowRecord  # noqa: F401
from mesh_platform.models.reputation import ReputationEvent, ReputationSnapshot  # noqa: F401
from mesh_platform.models.agent import AgentDefinition, AgentStatusLog  # noqa: F401
from mesh_platform.models.payment import PaymentIntent, PaymentWebhookEvent, Settlement  # noqa: F401

from mesh_platform.services.analytics_service import (
    get_agent_metrics,
    get_economic_health,
    get_order_timeline,
)


# ---------------------------------------------------------------------------
# Constants and strategies
# ---------------------------------------------------------------------------

WORKSPACE_ID = "ws-test-analytics"
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

agent_id_st = st.text(
    alphabet="abcdef0123456789", min_size=8, max_size=16
).filter(lambda s: len(s) >= 8)

tx_type_st = st.sampled_from(["payment", "escrow_lock", "escrow_release", "burn", "transfer"])

amount_st = st.floats(min_value=0.01, max_value=99999.99, allow_nan=False, allow_infinity=False)


# ---------------------------------------------------------------------------
# Composite strategies
# ---------------------------------------------------------------------------

@st.composite
def order_events_st(draw):
    """Generate a list of OrderEvent-like dicts for a single workspace.

    Timestamps are generated within the last 29 days relative to now so they
    fall inside the analytics service's default time window.
    """
    num_agents = draw(st.integers(min_value=1, max_value=5))
    agents = list(set(draw(agent_id_st) for _ in range(num_agents)))
    if not agents:
        agents = ["agent001"]

    num_orders = draw(st.integers(min_value=1, max_value=10))
    orders = [str(draw(st.uuids())) for _ in range(num_orders)]

    event_types = ["request", "bid", "negotiate", "commit", "execute", "verify", "settled"]
    # Use recent timestamps so they fall within the analytics cutoff window
    now = datetime.now(timezone.utc)
    events = []
    num_events = draw(st.integers(min_value=1, max_value=30))

    for _ in range(num_events):
        agent = draw(st.sampled_from(agents))
        order = draw(st.sampled_from(orders))
        event_type = draw(st.sampled_from(event_types))
        # Generate timestamps within the last 29 days
        offset_seconds = draw(st.integers(min_value=0, max_value=86400 * 29))
        occurred_at = now - timedelta(seconds=offset_seconds)
        events.append({
            "agent_id": agent,
            "order_id": order,
            "event_type": event_type,
            "occurred_at": occurred_at,
        })

    return events


@st.composite
def ledger_entries_st(draw):
    """Generate a list of LedgerEntry-like dicts for a single workspace.

    Timestamps are generated within the last 29 days relative to now.
    """
    num_entries = draw(st.integers(min_value=0, max_value=25))
    now = datetime.now(timezone.utc)
    entries = []

    for _ in range(num_entries):
        tx_type = draw(tx_type_st)
        amount = round(draw(amount_st), 2)
        from_agent = draw(agent_id_st)
        to_agent = draw(agent_id_st)
        offset_seconds = draw(st.integers(min_value=0, max_value=86400 * 29))
        recorded_at = now - timedelta(seconds=offset_seconds)
        entries.append({
            "tx_type": tx_type,
            "amount": amount,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "recorded_at": recorded_at,
        })

    return entries


# ---------------------------------------------------------------------------
# Async DB helpers (per-test isolation)
# ---------------------------------------------------------------------------

async def create_test_db():
    """Create a fresh in-memory SQLite engine and session factory.

    Uses StaticPool to ensure all sessions share the same underlying connection,
    which is required for in-memory SQLite (data is per-connection).
    """
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    return engine, session_factory


async def seed_workspace(session: AsyncSession) -> str:
    """Create a minimal user + workspace. Returns workspace_id."""
    user_id = str(uuid.uuid4())
    session.add(User(
        id=user_id,
        email=f"test-{user_id[:8]}@mesh.io",
        password_hash="fakehash",
        display_name="Test User",
    ))
    session.add(Workspace(
        id=WORKSPACE_ID,
        slug=f"test-ws-{user_id[:8]}",
        name="Test Workspace",
        owner_id=user_id,
    ))
    await session.flush()
    return WORKSPACE_ID


async def seed_order_events(
    session: AsyncSession, workspace_id: str, events: list[dict]
) -> None:
    """Insert Order and OrderEvent records from generated data."""
    order_ids = {e["order_id"] for e in events}
    for oid in order_ids:
        session.add(Order(
            id=oid,
            workspace_id=workspace_id,
            goods="test-goods",
            quantity=1,
            max_price_per_unit=100.0,
        ))
    await session.flush()

    for e in events:
        session.add(OrderEvent(
            order_id=e["order_id"],
            workspace_id=workspace_id,
            event_type=e["event_type"],
            agent_id=e["agent_id"],
            occurred_at=e["occurred_at"],
            mqtt_message_id=f"mqtt-{uuid.uuid4()}",
        ))
    await session.flush()


async def seed_ledger_entries(
    session: AsyncSession, workspace_id: str, entries: list[dict]
) -> None:
    """Insert LedgerEntry records from generated data."""
    for entry in entries:
        session.add(LedgerEntry(
            workspace_id=workspace_id,
            tx_type=entry["tx_type"],
            from_agent=entry["from_agent"],
            to_agent=entry["to_agent"],
            amount=entry["amount"],
            recorded_at=entry["recorded_at"],
        ))
    await session.flush()


# ---------------------------------------------------------------------------
# Manual expected-value computation (the "oracle")
# ---------------------------------------------------------------------------

def compute_expected_agent_order_counts(events: list[dict]) -> dict[str, int]:
    """Per-agent distinct order counts from raw event data."""
    agent_orders: dict[str, set[str]] = defaultdict(set)
    for e in events:
        agent_orders[e["agent_id"]].add(e["order_id"])
    return {agent: len(oids) for agent, oids in agent_orders.items()}


def compute_expected_economic_health(entries: list[dict]) -> dict:
    """Expected economic health metrics from raw ledger data."""
    if not entries:
        return {
            "total_volume": 0.0,
            "avg_transaction_size": 0.0,
            "transaction_count": 0,
            "burn_amount": 0.0,
            "tx_type_counts": {},
        }

    total_volume = sum(e["amount"] for e in entries)
    transaction_count = len(entries)
    avg_transaction_size = total_volume / transaction_count
    burn_amount = sum(e["amount"] for e in entries if e["tx_type"] == "burn")

    tx_type_counts: dict[str, int] = defaultdict(int)
    for e in entries:
        tx_type_counts[e["tx_type"]] += 1

    return {
        "total_volume": total_volume,
        "avg_transaction_size": avg_transaction_size,
        "transaction_count": transaction_count,
        "burn_amount": burn_amount,
        "tx_type_counts": dict(tx_type_counts),
    }


# ---------------------------------------------------------------------------
# Async test runner helper
# ---------------------------------------------------------------------------

def run_async(coro):
    """Run an async coroutine in a new event loop (Python 3.14 compatible)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Property 1 — Analytics aggregation correctness
# ---------------------------------------------------------------------------

class TestAnalyticsAggregationCorrectness:
    """Property 1: Analytics aggregation correctness.

    *For any* set of OrderEvent and LedgerEntry records in a workspace within
    a time range, the analytics service SHALL compute:
    - Per-agent order counts equal to the count of distinct order IDs in their events
    - Total ledger volume equal to the sum of all LedgerEntry amounts
    - Average transaction size equal to total volume divided by transaction count

    **Validates: Requirements 1.1, 1.3**
    """

    @given(events=order_events_st())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_per_agent_order_counts_match_distinct_order_ids(
        self, events: list[dict]
    ) -> None:
        """Per-agent order counts equal the count of distinct order IDs in their events.

        **Validates: Requirements 1.1**
        """
        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    workspace_id = await seed_workspace(session)
                    await seed_order_events(session, workspace_id, events)
                    await session.commit()

                async with session_factory() as session:
                    result = await get_agent_metrics(session, workspace_id, days=365)

                expected_counts = compute_expected_agent_order_counts(events)
                result_counts = {m["agent_id"]: m["total_orders"] for m in result}

                for agent_id, expected_count in expected_counts.items():
                    assert agent_id in result_counts, (
                        f"Agent '{agent_id}' missing from analytics results"
                    )
                    assert result_counts[agent_id] == expected_count, (
                        f"Agent '{agent_id}': expected {expected_count} orders, "
                        f"got {result_counts[agent_id]}"
                    )

                assert set(result_counts.keys()) == set(expected_counts.keys()), (
                    f"Agent sets differ: result={set(result_counts.keys())}, "
                    f"expected={set(expected_counts.keys())}"
                )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())

    @given(entries=ledger_entries_st())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_total_ledger_volume_equals_sum_of_amounts(
        self, entries: list[dict]
    ) -> None:
        """Total ledger volume equals the sum of all LedgerEntry amounts.

        **Validates: Requirements 1.3**
        """
        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    workspace_id = await seed_workspace(session)
                    await seed_ledger_entries(session, workspace_id, entries)
                    await session.commit()

                async with session_factory() as session:
                    result = await get_economic_health(session, workspace_id, days=365)

                expected = compute_expected_economic_health(entries)

                assert abs(result["total_volume"] - round(expected["total_volume"], 2)) < 0.02, (
                    f"Total volume: expected ~{expected['total_volume']:.2f}, "
                    f"got {result['total_volume']}"
                )
                assert result["transaction_count"] == expected["transaction_count"], (
                    f"Transaction count: expected {expected['transaction_count']}, "
                    f"got {result['transaction_count']}"
                )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())

    @given(entries=ledger_entries_st())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_avg_transaction_size_equals_volume_divided_by_count(
        self, entries: list[dict]
    ) -> None:
        """Average transaction size equals total volume divided by transaction count.

        **Validates: Requirements 1.3**
        """
        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    workspace_id = await seed_workspace(session)
                    await seed_ledger_entries(session, workspace_id, entries)
                    await session.commit()

                async with session_factory() as session:
                    result = await get_economic_health(session, workspace_id, days=365)

                expected = compute_expected_economic_health(entries)

                if expected["transaction_count"] == 0:
                    assert result["avg_transaction_size"] == 0.0, (
                        f"Expected 0.0 avg when no entries, got {result['avg_transaction_size']}"
                    )
                else:
                    expected_avg = round(
                        expected["total_volume"] / expected["transaction_count"], 2
                    )
                    assert abs(result["avg_transaction_size"] - expected_avg) < 0.02, (
                        f"Avg transaction size: expected ~{expected_avg}, "
                        f"got {result['avg_transaction_size']}"
                    )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())

    @given(entries=ledger_entries_st())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_burn_amount_equals_sum_of_burn_entries(
        self, entries: list[dict]
    ) -> None:
        """Burn amount equals the sum of amounts where tx_type is 'burn'.

        **Validates: Requirements 1.3**
        """
        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    workspace_id = await seed_workspace(session)
                    await seed_ledger_entries(session, workspace_id, entries)
                    await session.commit()

                async with session_factory() as session:
                    result = await get_economic_health(session, workspace_id, days=365)

                expected = compute_expected_economic_health(entries)

                assert abs(result["burn_amount"] - round(expected["burn_amount"], 2)) < 0.02, (
                    f"Burn amount: expected ~{expected['burn_amount']:.2f}, "
                    f"got {result['burn_amount']}"
                )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())

    @given(entries=ledger_entries_st())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_tx_type_counts_match_manual_grouping(
        self, entries: list[dict]
    ) -> None:
        """Transaction type counts match manual grouping of entries by tx_type.

        **Validates: Requirements 1.3**
        """
        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    workspace_id = await seed_workspace(session)
                    await seed_ledger_entries(session, workspace_id, entries)
                    await session.commit()

                async with session_factory() as session:
                    result = await get_economic_health(session, workspace_id, days=365)

                expected = compute_expected_economic_health(entries)

                assert result["tx_type_counts"] == expected["tx_type_counts"], (
                    f"tx_type_counts: expected {expected['tx_type_counts']}, "
                    f"got {result['tx_type_counts']}"
                )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())


# ---------------------------------------------------------------------------
# Strategy for Property 2 — Order lifecycle duration computation
# ---------------------------------------------------------------------------

EVENT_PHASES = ["request", "bid", "negotiate", "commit", "execute", "verify", "settled"]


@st.composite
def single_order_events_st(draw):
    """Generate a sequence of OrderEvent-like dicts for a single order.

    Produces events with strictly increasing timestamps so the ordering is
    deterministic and the expected durations can be computed exactly.
    """
    order_id = str(draw(st.uuids()))
    agent_id = draw(agent_id_st)

    # Generate between 2 and 8 events (need at least 2 for a phase transition)
    num_events = draw(st.integers(min_value=2, max_value=8))

    # Pick event types for each step
    event_types = [draw(st.sampled_from(EVENT_PHASES)) for _ in range(num_events)]

    # Build strictly increasing timestamps within the last 29 days.
    # Start from a base time and add cumulative positive deltas.
    now = datetime.now(timezone.utc)
    base_offset = draw(st.integers(min_value=3600, max_value=86400 * 28))
    base_time = now - timedelta(seconds=base_offset)

    timestamps = [base_time]
    for _ in range(num_events - 1):
        delta = draw(st.integers(min_value=1, max_value=3600))
        timestamps.append(timestamps[-1] + timedelta(seconds=delta))

    events = []
    for i in range(num_events):
        events.append({
            "agent_id": agent_id,
            "order_id": order_id,
            "event_type": event_types[i],
            "occurred_at": timestamps[i],
        })

    return events


# ---------------------------------------------------------------------------
# Oracle for Property 2
# ---------------------------------------------------------------------------

def compute_expected_timeline(events: list[dict]) -> dict:
    """Compute expected order timeline from raw event data.

    Returns a dict with order_id, phases list, and total_duration.
    Events must be pre-sorted by occurred_at (ascending).
    """
    sorted_events = sorted(events, key=lambda e: e["occurred_at"])
    order_id = sorted_events[0]["order_id"]

    phases = []
    for i in range(1, len(sorted_events)):
        prev = sorted_events[i - 1]
        curr = sorted_events[i]
        duration = (curr["occurred_at"] - prev["occurred_at"]).total_seconds()
        phases.append({
            "from": prev["event_type"],
            "to": curr["event_type"],
            "duration_seconds": round(duration, 2),
        })

    total_duration = (
        sorted_events[-1]["occurred_at"] - sorted_events[0]["occurred_at"]
    ).total_seconds()

    return {
        "order_id": order_id,
        "phases": phases,
        "total_duration": round(total_duration, 2),
    }


# ---------------------------------------------------------------------------
# Property 2 — Order lifecycle duration computation
# ---------------------------------------------------------------------------

class TestOrderLifecycleDurationComputation:
    """Property 2: Order lifecycle duration computation.

    *For any* order with a sequence of OrderEvent records with known timestamps,
    the timeline service SHALL compute the duration between consecutive phase
    transitions as the difference in seconds between their `occurred_at`
    timestamps, and the sum of all phase durations SHALL equal the total time
    from first to last event.

    **Validates: Requirements 1.2**
    """

    @given(events=single_order_events_st())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_phase_durations_equal_timestamp_differences(
        self, events: list[dict]
    ) -> None:
        """Each phase duration equals the difference between consecutive timestamps.

        **Validates: Requirements 1.2**
        """
        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    workspace_id = await seed_workspace(session)
                    await seed_order_events(session, workspace_id, events)
                    await session.commit()

                async with session_factory() as session:
                    result = await get_order_timeline(session, workspace_id, days=365)

                expected = compute_expected_timeline(events)

                # Should have exactly one order in the result
                assert len(result) == 1, (
                    f"Expected 1 order in timeline, got {len(result)}"
                )

                order_result = result[0]
                assert order_result["order_id"] == expected["order_id"], (
                    f"Order ID mismatch: {order_result['order_id']} != {expected['order_id']}"
                )

                # Verify each phase duration matches expected
                assert len(order_result["phases"]) == len(expected["phases"]), (
                    f"Phase count mismatch: {len(order_result['phases'])} != "
                    f"{len(expected['phases'])}"
                )

                for i, (actual_phase, expected_phase) in enumerate(
                    zip(order_result["phases"], expected["phases"])
                ):
                    assert actual_phase["from"] == expected_phase["from"], (
                        f"Phase {i} 'from' mismatch: "
                        f"{actual_phase['from']} != {expected_phase['from']}"
                    )
                    assert actual_phase["to"] == expected_phase["to"], (
                        f"Phase {i} 'to' mismatch: "
                        f"{actual_phase['to']} != {expected_phase['to']}"
                    )
                    assert abs(
                        actual_phase["duration_seconds"]
                        - expected_phase["duration_seconds"]
                    ) < 0.01, (
                        f"Phase {i} duration mismatch: "
                        f"{actual_phase['duration_seconds']} != "
                        f"{expected_phase['duration_seconds']}"
                    )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())

    @given(events=single_order_events_st())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_sum_of_phase_durations_equals_total_time(
        self, events: list[dict]
    ) -> None:
        """Sum of all phase durations equals total time from first to last event.

        **Validates: Requirements 1.2**
        """
        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    workspace_id = await seed_workspace(session)
                    await seed_order_events(session, workspace_id, events)
                    await session.commit()

                async with session_factory() as session:
                    result = await get_order_timeline(session, workspace_id, days=365)

                expected = compute_expected_timeline(events)

                assert len(result) == 1, (
                    f"Expected 1 order in timeline, got {len(result)}"
                )

                order_result = result[0]
                sum_of_durations = sum(
                    p["duration_seconds"] for p in order_result["phases"]
                )

                assert abs(sum_of_durations - expected["total_duration"]) < 0.1, (
                    f"Sum of phase durations ({sum_of_durations}) != "
                    f"total time ({expected['total_duration']})"
                )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())
