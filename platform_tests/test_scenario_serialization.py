"""Property-based test for scenario serialization round-trip.

**Feature: saas-platform-enhancements, Property 4: Scenario serialization round-trip**
**Validates: Requirements 3.1, 3.4**

*For any* valid scenario definition (containing agents, goods, orders, and optional
chaos events), serializing the definition to JSON and deserializing it back SHALL
produce an object equal to the original definition.
"""

from __future__ import annotations

from hypothesis import given, settings, strategies as st

from mesh_platform.schemas.scenario import (
    AgentConfig,
    ChaosEventConfig,
    GoodsDefinition,
    OrderConfig,
    ScenarioDefinition,
)
from mesh_platform.services.scenario_service import (
    _deserialize_definition,
    _serialize_definition,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies for generating valid scenario components
# ---------------------------------------------------------------------------

non_empty_text_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=50,
).filter(lambda s: s.strip())

capability_st = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz_-",
    min_size=1,
    max_size=20,
)

agent_config_st = st.builds(
    AgentConfig,
    role=st.sampled_from(["buyer", "supplier", "logistics", "inspector", "oracle"]),
    count=st.integers(min_value=1, max_value=50),
    initial_balance=st.floats(min_value=0.0, max_value=1_000_000.0, allow_nan=False,
                              allow_infinity=False),
    capabilities=st.lists(capability_st, min_size=0, max_size=5),
)

goods_definition_st = st.builds(
    GoodsDefinition,
    name=non_empty_text_st,
    category=non_empty_text_st,
    base_price=st.floats(min_value=0.01, max_value=1_000_000.0, allow_nan=False,
                         allow_infinity=False),
    volatility=st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0,
                                               allow_nan=False, allow_infinity=False)),
)

order_config_st = st.builds(
    OrderConfig,
    at_second=st.integers(min_value=0, max_value=86400),
    goods=non_empty_text_st,
    category=non_empty_text_st,
    quantity=st.integers(min_value=1, max_value=10000),
    max_price_per_unit=st.floats(min_value=0.01, max_value=1_000_000.0, allow_nan=False,
                                 allow_infinity=False),
    quality_threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False,
                                allow_infinity=False),
)

chaos_event_st = st.builds(
    ChaosEventConfig,
    at_second=st.integers(min_value=0, max_value=86400),
    event_type=st.sampled_from(["kill_agent", "network_partition", "delay", "corrupt_message"]),
    target=st.sampled_from(["buyer", "supplier", "logistics", "inspector", "oracle"]),
)


@st.composite
def valid_scenario_definition_st(draw):
    """Generate a valid ScenarioDefinition with at least one buyer, one supplier,
    and one goods definition.

    This ensures the generated definition passes the model_validator constraints.
    """
    # Guarantee at least one buyer and one supplier
    buyer = draw(st.builds(
        AgentConfig,
        role=st.just("buyer"),
        count=st.integers(min_value=1, max_value=10),
        initial_balance=st.floats(min_value=0.0, max_value=1_000_000.0,
                                  allow_nan=False, allow_infinity=False),
        capabilities=st.lists(capability_st, min_size=0, max_size=5),
    ))
    supplier = draw(st.builds(
        AgentConfig,
        role=st.just("supplier"),
        count=st.integers(min_value=1, max_value=10),
        initial_balance=st.floats(min_value=0.0, max_value=1_000_000.0,
                                  allow_nan=False, allow_infinity=False),
        capabilities=st.lists(capability_st, min_size=0, max_size=5),
    ))

    # Optionally add more agents of any role
    extra_agents = draw(st.lists(agent_config_st, min_size=0, max_size=5))
    agents = [buyer, supplier] + extra_agents

    # At least one goods definition
    first_goods = draw(goods_definition_st)
    extra_goods = draw(st.lists(goods_definition_st, min_size=0, max_size=5))
    goods = [first_goods] + extra_goods

    # Optional orders and chaos events
    orders = draw(st.lists(order_config_st, min_size=0, max_size=5))
    chaos_events = draw(st.lists(chaos_event_st, min_size=0, max_size=3))

    return ScenarioDefinition(
        agents=agents,
        goods=goods,
        orders=orders,
        chaos_events=chaos_events,
    )


# ---------------------------------------------------------------------------
# Property 4 — Scenario serialization round-trip
# ---------------------------------------------------------------------------

class TestScenarioSerializationRoundTrip:
    """Property 4: Scenario serialization round-trip.

    *For any* valid scenario definition (containing agents, goods, orders, and
    optional chaos events), serializing the definition to JSON and deserializing
    it back SHALL produce an object equal to the original definition.

    **Validates: Requirements 3.1, 3.4**
    """

    @given(definition=valid_scenario_definition_st())
    @settings(max_examples=100, deadline=None)
    def test_serialize_deserialize_produces_equal_object(
        self, definition: ScenarioDefinition
    ) -> None:
        """Serializing to JSON and deserializing back produces an equal object.

        **Validates: Requirements 3.1, 3.4**
        """
        json_str = _serialize_definition(definition)
        restored = _deserialize_definition(json_str)

        assert restored == definition, (
            f"Round-trip mismatch.\n"
            f"Original: {definition}\n"
            f"Restored: {restored}"
        )

    @given(definition=valid_scenario_definition_st())
    @settings(max_examples=100, deadline=None)
    def test_serialized_json_is_valid_string(
        self, definition: ScenarioDefinition
    ) -> None:
        """Serialization produces a non-empty JSON string.

        **Validates: Requirements 3.1, 3.4**
        """
        import json

        json_str = _serialize_definition(definition)

        # Must be a non-empty string
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # Must be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

        # Must contain the expected top-level keys
        assert "agents" in parsed
        assert "goods" in parsed

    @given(definition=valid_scenario_definition_st())
    @settings(max_examples=100, deadline=None)
    def test_round_trip_preserves_agent_count(
        self, definition: ScenarioDefinition
    ) -> None:
        """Round-trip preserves the number of agent configurations.

        **Validates: Requirements 3.1, 3.4**
        """
        json_str = _serialize_definition(definition)
        restored = _deserialize_definition(json_str)

        assert len(restored.agents) == len(definition.agents), (
            f"Agent count mismatch: original={len(definition.agents)}, "
            f"restored={len(restored.agents)}"
        )

    @given(definition=valid_scenario_definition_st())
    @settings(max_examples=100, deadline=None)
    def test_round_trip_preserves_goods_definitions(
        self, definition: ScenarioDefinition
    ) -> None:
        """Round-trip preserves all goods definitions including prices.

        **Validates: Requirements 3.1, 3.4**
        """
        json_str = _serialize_definition(definition)
        restored = _deserialize_definition(json_str)

        assert len(restored.goods) == len(definition.goods), (
            f"Goods count mismatch: original={len(definition.goods)}, "
            f"restored={len(restored.goods)}"
        )

        for i, (orig, rest) in enumerate(zip(definition.goods, restored.goods)):
            assert rest.name == orig.name, (
                f"Goods[{i}] name mismatch: '{orig.name}' != '{rest.name}'"
            )
            assert rest.category == orig.category, (
                f"Goods[{i}] category mismatch: '{orig.category}' != '{rest.category}'"
            )
            assert rest.base_price == orig.base_price, (
                f"Goods[{i}] base_price mismatch: {orig.base_price} != {rest.base_price}"
            )

    @given(definition=valid_scenario_definition_st())
    @settings(max_examples=100, deadline=None)
    def test_round_trip_preserves_orders_and_chaos_events(
        self, definition: ScenarioDefinition
    ) -> None:
        """Round-trip preserves orders and chaos events lists.

        **Validates: Requirements 3.1, 3.4**
        """
        json_str = _serialize_definition(definition)
        restored = _deserialize_definition(json_str)

        assert len(restored.orders) == len(definition.orders), (
            f"Orders count mismatch: original={len(definition.orders)}, "
            f"restored={len(restored.orders)}"
        )
        assert len(restored.chaos_events) == len(definition.chaos_events), (
            f"Chaos events count mismatch: original={len(definition.chaos_events)}, "
            f"restored={len(restored.chaos_events)}"
        )

        for i, (orig, rest) in enumerate(zip(definition.orders, restored.orders)):
            assert rest == orig, f"Order[{i}] mismatch after round-trip"

        for i, (orig, rest) in enumerate(
            zip(definition.chaos_events, restored.chaos_events)
        ):
            assert rest == orig, f"ChaosEvent[{i}] mismatch after round-trip"
