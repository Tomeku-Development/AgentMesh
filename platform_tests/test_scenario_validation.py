"""Property-based test for scenario validation rejects invalid definitions.

**Feature: saas-platform-enhancements, Property 5: Scenario validation rejects invalid definitions**
**Validates: Requirements 3.2, 3.7**

*For any* scenario definition missing a buyer agent, missing a supplier agent,
missing all goods definitions, or containing a goods definition with an empty name,
empty category, or base_price ≤ 0, the validation SHALL reject the definition.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st
from pydantic import ValidationError

from mesh_platform.schemas.scenario import (
    AgentConfig,
    GoodsDefinition,
    ScenarioDefinition,
)


# ---------------------------------------------------------------------------
# Reusable strategies
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

valid_goods_st = st.builds(
    GoodsDefinition,
    name=non_empty_text_st,
    category=non_empty_text_st,
    base_price=st.floats(min_value=0.01, max_value=1_000_000.0,
                         allow_nan=False, allow_infinity=False),
    volatility=st.one_of(
        st.none(),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    ),
)


def _make_agent(role: str, **overrides) -> AgentConfig:
    """Helper to build an AgentConfig with sensible defaults."""
    defaults = dict(role=role, count=1, initial_balance=5000.0, capabilities=[])
    defaults.update(overrides)
    return AgentConfig(**defaults)


# Strategy for non-buyer, non-supplier roles only
non_buyer_role_st = st.sampled_from(["supplier", "logistics", "inspector", "oracle"])
non_supplier_role_st = st.sampled_from(["buyer", "logistics", "inspector", "oracle"])


# ---------------------------------------------------------------------------
# Property 5 — Scenario validation rejects invalid definitions
# ---------------------------------------------------------------------------


class TestScenarioValidationRejectsInvalid:
    """Property 5: Scenario validation rejects invalid definitions.

    *For any* scenario definition missing a buyer agent, missing a supplier agent,
    missing all goods definitions, or containing a goods definition with an empty
    name, empty category, or base_price ≤ 0, the validation SHALL reject the
    definition.

    **Validates: Requirements 3.2, 3.7**
    """

    # ── 1. No buyer agent ──────────────────────────────────────────────

    @given(
        extra_roles=st.lists(non_buyer_role_st, min_size=0, max_size=5),
        goods=st.lists(valid_goods_st, min_size=1, max_size=3),
    )
    @settings(max_examples=100, deadline=None)
    def test_no_buyer_agent_rejected(
        self, extra_roles: list[str], goods: list[GoodsDefinition]
    ) -> None:
        """Definitions with no buyer agent SHALL be rejected.

        **Validates: Requirements 3.2**
        """
        # Build agents list that is guaranteed to have no buyer
        agents = [_make_agent(role) for role in extra_roles]
        # Ensure at least one supplier so the only violation is missing buyer
        if not any(a.role == "supplier" for a in agents):
            agents.append(_make_agent("supplier"))

        with pytest.raises(ValidationError):
            ScenarioDefinition(agents=agents, goods=goods)

    # ── 2. No supplier agent ───────────────────────────────────────────

    @given(
        extra_roles=st.lists(non_supplier_role_st, min_size=0, max_size=5),
        goods=st.lists(valid_goods_st, min_size=1, max_size=3),
    )
    @settings(max_examples=100, deadline=None)
    def test_no_supplier_agent_rejected(
        self, extra_roles: list[str], goods: list[GoodsDefinition]
    ) -> None:
        """Definitions with no supplier agent SHALL be rejected.

        **Validates: Requirements 3.2**
        """
        agents = [_make_agent(role) for role in extra_roles]
        # Ensure at least one buyer so the only violation is missing supplier
        if not any(a.role == "buyer" for a in agents):
            agents.append(_make_agent("buyer"))

        with pytest.raises(ValidationError):
            ScenarioDefinition(agents=agents, goods=goods)

    # ── 3. Empty goods list ────────────────────────────────────────────

    @given(
        extra_roles=st.lists(
            st.sampled_from(["logistics", "inspector", "oracle"]),
            min_size=0,
            max_size=3,
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_empty_goods_list_rejected(self, extra_roles: list[str]) -> None:
        """Definitions with an empty goods list SHALL be rejected.

        **Validates: Requirements 3.2**
        """
        agents = [_make_agent("buyer"), _make_agent("supplier")]
        agents.extend(_make_agent(r) for r in extra_roles)

        with pytest.raises(ValidationError):
            ScenarioDefinition(agents=agents, goods=[])

    # ── 4. Goods with empty name ───────────────────────────────────────

    @given(
        category=non_empty_text_st,
        base_price=st.floats(min_value=0.01, max_value=1_000_000.0,
                             allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_goods_empty_name_rejected(
        self, category: str, base_price: float
    ) -> None:
        """Goods definitions with an empty name SHALL be rejected.

        **Validates: Requirements 3.7**
        """
        with pytest.raises(ValidationError):
            GoodsDefinition(name="", category=category, base_price=base_price)

    # ── 5. Goods with empty category ───────────────────────────────────

    @given(
        name=non_empty_text_st,
        base_price=st.floats(min_value=0.01, max_value=1_000_000.0,
                             allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_goods_empty_category_rejected(
        self, name: str, base_price: float
    ) -> None:
        """Goods definitions with an empty category SHALL be rejected.

        **Validates: Requirements 3.7**
        """
        with pytest.raises(ValidationError):
            GoodsDefinition(name=name, category="", base_price=base_price)

    # ── 6. Goods with base_price ≤ 0 ──────────────────────────────────

    @given(
        name=non_empty_text_st,
        category=non_empty_text_st,
        bad_price=st.floats(
            min_value=-1_000_000.0, max_value=0.0,
            allow_nan=False, allow_infinity=False,
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_goods_non_positive_price_rejected(
        self, name: str, category: str, bad_price: float
    ) -> None:
        """Goods definitions with base_price ≤ 0 SHALL be rejected.

        **Validates: Requirements 3.7**
        """
        with pytest.raises(ValidationError):
            GoodsDefinition(name=name, category=category, base_price=bad_price)
