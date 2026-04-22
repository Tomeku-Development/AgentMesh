"""Property-based tests for marketplace search filtering and ordering.

**Feature: saas-platform-enhancements, Property 9: Marketplace search returns filtered and ordered results**
**Validates: Requirements 6.2**
"""

from __future__ import annotations

import asyncio
import json
import uuid

from hypothesis import given, settings, strategies as st, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from mesh_platform.models.base import Base
from mesh_platform.models.user import User, APIKey  # noqa: F401
from mesh_platform.models.workspace import Workspace, WorkspaceMembership
from mesh_platform.models.order import Order, OrderEvent  # noqa: F401
from mesh_platform.models.ledger import LedgerEntry, EscrowRecord  # noqa: F401
from mesh_platform.models.reputation import ReputationEvent, ReputationSnapshot  # noqa: F401
from mesh_platform.models.agent import AgentDefinition, AgentStatusLog  # noqa: F401
from mesh_platform.models.payment import PaymentIntent, PaymentWebhookEvent, Settlement  # noqa: F401
from mesh_platform.models.scenario import Scenario  # noqa: F401
from mesh_platform.models.marketplace import AgentTemplate

from mesh_platform.schemas.marketplace import InstantiateRequest
from mesh_platform.services.marketplace_service import instantiate_template, search_templates


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

AGENT_ROLES = ["buyer", "supplier", "logistics", "inspector", "oracle"]
CAPABILITIES_POOL = [
    "electronics", "food", "metals", "plastics", "textiles",
    "chemicals", "machinery", "automotive", "pharma", "energy",
]


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

name_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs")),
    min_size=3,
    max_size=50,
).filter(lambda s: len(s.strip()) >= 3)

role_st = st.sampled_from(AGENT_ROLES)

capabilities_st = st.lists(
    st.sampled_from(CAPABILITIES_POOL),
    min_size=0,
    max_size=5,
    unique=True,
)

usage_count_st = st.integers(min_value=0, max_value=10000)


@st.composite
def agent_template_st(draw):
    """Generate a single AgentTemplate-like dict with random attributes."""
    name = draw(name_st)
    role = draw(role_st)
    capabilities = draw(capabilities_st)
    usage_count = draw(usage_count_st)
    description = draw(st.text(min_size=0, max_size=100) | st.none())

    return {
        "name": name,
        "agent_role": role,
        "capabilities": capabilities,
        "usage_count": usage_count,
        "description": description,
        "default_initial_balance": 1000.0,
        "config": {},
    }


@st.composite
def template_set_st(draw):
    """Generate a set of 1-15 AgentTemplate dicts with unique names."""
    num_templates = draw(st.integers(min_value=1, max_value=15))
    templates = []
    seen_names = set()

    for _ in range(num_templates):
        tmpl = draw(agent_template_st())
        # Ensure unique names by appending a suffix if needed
        base_name = tmpl["name"]
        while tmpl["name"] in seen_names:
            tmpl["name"] = base_name + draw(
                st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=2, max_size=4)
            )
            # Ensure name stays within 3-100 chars
            if len(tmpl["name"]) > 100:
                tmpl["name"] = tmpl["name"][:100]
        seen_names.add(tmpl["name"])
        templates.append(tmpl)

    return templates


@st.composite
def search_filter_st(draw):
    """Generate a search filter: either a role filter, a capability filter, or both."""
    use_role = draw(st.booleans())
    use_capability = draw(st.booleans())

    role = draw(role_st) if use_role else None
    capability = draw(st.sampled_from(CAPABILITIES_POOL)) if use_capability else None

    return {"role": role, "capability": capability}


# ---------------------------------------------------------------------------
# Async DB helpers (per-test isolation)
# ---------------------------------------------------------------------------

async def create_test_db():
    """Create a fresh in-memory SQLite engine and session factory."""
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


async def seed_author(session: AsyncSession) -> str:
    """Create a minimal user to serve as template author. Returns user_id."""
    user_id = str(uuid.uuid4())
    session.add(User(
        id=user_id,
        email=f"author-{user_id[:8]}@mesh.io",
        password_hash="fakehash",
        display_name="Test Author",
    ))
    await session.flush()
    return user_id


async def seed_templates(
    session: AsyncSession, author_id: str, templates: list[dict]
) -> None:
    """Insert AgentTemplate records from generated data."""
    for i, tmpl in enumerate(templates):
        session.add(AgentTemplate(
            id=str(uuid.uuid4()),
            name=tmpl["name"],
            description=tmpl["description"],
            agent_role=tmpl["agent_role"],
            capabilities_json=json.dumps(tmpl["capabilities"]),
            default_initial_balance=tmpl["default_initial_balance"],
            config_json=json.dumps(tmpl["config"]),
            author_id=author_id,
            usage_count=tmpl["usage_count"],
        ))
    await session.flush()


# ---------------------------------------------------------------------------
# Oracle: compute expected results manually
# ---------------------------------------------------------------------------

def compute_expected_results(
    templates: list[dict],
    role: str | None = None,
    capability: str | None = None,
) -> list[dict]:
    """Filter and sort templates the same way the service should.

    Returns templates matching the filter, ordered by usage_count DESC.
    """
    results = list(templates)

    if role is not None:
        results = [t for t in results if t["agent_role"] == role]

    if capability is not None:
        results = [t for t in results if capability in t["capabilities"]]

    # Sort by usage_count descending
    results.sort(key=lambda t: t["usage_count"], reverse=True)

    return results


# ---------------------------------------------------------------------------
# Async test runner helper
# ---------------------------------------------------------------------------

def run_async(coro):
    """Run an async coroutine in a new event loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Property 9 — Marketplace search returns filtered and ordered results
# ---------------------------------------------------------------------------

class TestMarketplaceSearchFilteringAndOrdering:
    """Property 9: Marketplace search returns filtered and ordered results.

    *For any* set of agent templates and *for any* search filter (by role or
    capability), all returned templates SHALL match the filter criteria, and
    results SHALL be ordered by usage_count descending.

    **Validates: Requirements 6.2**
    """

    @given(templates=template_set_st(), search_filter=search_filter_st())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_all_returned_templates_match_role_filter(
        self, templates: list[dict], search_filter: dict
    ) -> None:
        """When filtering by role, all returned templates have the requested role.

        **Validates: Requirements 6.2**
        """
        role = search_filter["role"]
        capability = search_filter["capability"]

        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    author_id = await seed_author(session)
                    await seed_templates(session, author_id, templates)
                    await session.commit()

                async with session_factory() as session:
                    results = await search_templates(
                        session, role=role, capability=capability
                    )

                # All returned templates must match the role filter
                if role is not None:
                    for r in results:
                        assert r.agent_role == role, (
                            f"Template '{r.name}' has role '{r.agent_role}', "
                            f"expected '{role}'"
                        )

                # All returned templates must match the capability filter
                if capability is not None:
                    for r in results:
                        assert capability in r.capabilities, (
                            f"Template '{r.name}' capabilities {r.capabilities} "
                            f"do not contain '{capability}'"
                        )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())

    @given(templates=template_set_st(), search_filter=search_filter_st())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_results_ordered_by_usage_count_descending(
        self, templates: list[dict], search_filter: dict
    ) -> None:
        """Results are ordered by usage_count descending.

        **Validates: Requirements 6.2**
        """
        role = search_filter["role"]
        capability = search_filter["capability"]

        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    author_id = await seed_author(session)
                    await seed_templates(session, author_id, templates)
                    await session.commit()

                async with session_factory() as session:
                    results = await search_templates(
                        session, role=role, capability=capability
                    )

                # Verify ordering: usage_count should be non-increasing
                usage_counts = [r.usage_count for r in results]
                for i in range(1, len(usage_counts)):
                    assert usage_counts[i - 1] >= usage_counts[i], (
                        f"Results not ordered by usage_count DESC: "
                        f"{usage_counts[i - 1]} < {usage_counts[i]} "
                        f"at positions {i - 1}, {i}. "
                        f"Full sequence: {usage_counts}"
                    )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())

    @given(templates=template_set_st(), search_filter=search_filter_st())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_result_count_matches_expected_filtered_count(
        self, templates: list[dict], search_filter: dict
    ) -> None:
        """The number of returned results matches the expected count from manual filtering.

        **Validates: Requirements 6.2**
        """
        role = search_filter["role"]
        capability = search_filter["capability"]

        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    author_id = await seed_author(session)
                    await seed_templates(session, author_id, templates)
                    await session.commit()

                async with session_factory() as session:
                    results = await search_templates(
                        session, role=role, capability=capability
                    )

                expected = compute_expected_results(templates, role=role, capability=capability)

                assert len(results) == len(expected), (
                    f"Result count mismatch: got {len(results)}, "
                    f"expected {len(expected)} "
                    f"(role={role}, capability={capability})"
                )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())

    @given(templates=template_set_st(), search_filter=search_filter_st())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_result_names_match_expected_filtered_names(
        self, templates: list[dict], search_filter: dict
    ) -> None:
        """The set of returned template names matches the expected set from manual filtering.

        **Validates: Requirements 6.2**
        """
        role = search_filter["role"]
        capability = search_filter["capability"]

        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    author_id = await seed_author(session)
                    await seed_templates(session, author_id, templates)
                    await session.commit()

                async with session_factory() as session:
                    results = await search_templates(
                        session, role=role, capability=capability
                    )

                expected = compute_expected_results(templates, role=role, capability=capability)

                result_names = {r.name for r in results}
                expected_names = {t["name"] for t in expected}

                assert result_names == expected_names, (
                    f"Name set mismatch: "
                    f"got {result_names}, expected {expected_names} "
                    f"(role={role}, capability={capability})"
                )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())


# ---------------------------------------------------------------------------
# Strategies for Property 10 — Template instantiation merge
# ---------------------------------------------------------------------------

initial_balance_st = st.floats(min_value=0.0, max_value=100_000.0, allow_nan=False, allow_infinity=False)

override_balance_st = st.one_of(st.none(), initial_balance_st)

override_capabilities_st = st.one_of(
    st.none(),
    st.lists(st.sampled_from(CAPABILITIES_POOL), min_size=0, max_size=5, unique=True),
)


@st.composite
def instantiate_override_st(draw):
    """Generate an InstantiateRequest with random overrides (some None, some with values)."""
    balance = draw(override_balance_st)
    caps = draw(override_capabilities_st)
    return InstantiateRequest(initial_balance=balance, capabilities=caps)


@st.composite
def template_for_instantiation_st(draw):
    """Generate a single AgentTemplate dict with known defaults for instantiation testing."""
    name = draw(name_st)
    role = draw(role_st)
    capabilities = draw(capabilities_st)
    balance = draw(initial_balance_st)

    return {
        "name": name,
        "agent_role": role,
        "capabilities": capabilities,
        "default_initial_balance": balance,
        "description": draw(st.text(min_size=0, max_size=100) | st.none()),
        "config": {},
    }


# ---------------------------------------------------------------------------
# Async helpers for Property 10
# ---------------------------------------------------------------------------

async def seed_workspace(session: AsyncSession, owner_id: str) -> str:
    """Create a minimal workspace. Returns workspace_id."""
    workspace_id = str(uuid.uuid4())
    session.add(Workspace(
        id=workspace_id,
        slug=f"ws-{workspace_id[:8]}",
        name="Test Workspace",
        owner_id=owner_id,
    ))
    await session.flush()
    return workspace_id


# ---------------------------------------------------------------------------
# Property 10 — Template instantiation merges defaults with overrides
# ---------------------------------------------------------------------------

class TestTemplateInstantiationMerge:
    """Property 10: Template instantiation merges defaults with overrides.

    *For any* agent template and *for any* set of parameter overrides, the
    resulting AgentDefinition SHALL use the override value for each overridden
    field and the template's default value for all non-overridden fields.

    **Validates: Requirements 6.4**
    """

    @given(
        template_data=template_for_instantiation_st(),
        overrides=instantiate_override_st(),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_overridden_fields_use_override_values(
        self, template_data: dict, overrides: InstantiateRequest
    ) -> None:
        """When overrides are provided, the AgentDefinition uses the override values.

        **Validates: Requirements 6.4**
        """

        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    author_id = await seed_author(session)
                    workspace_id = await seed_workspace(session, author_id)

                    # Create the template in the DB
                    template = AgentTemplate(
                        id=str(uuid.uuid4()),
                        name=template_data["name"],
                        description=template_data["description"],
                        agent_role=template_data["agent_role"],
                        capabilities_json=json.dumps(template_data["capabilities"]),
                        default_initial_balance=template_data["default_initial_balance"],
                        config_json=json.dumps(template_data["config"]),
                        author_id=author_id,
                        usage_count=0,
                    )
                    session.add(template)
                    await session.commit()

                    template_id = template.id

                async with session_factory() as session:
                    agent_def = await instantiate_template(
                        session, template_id, workspace_id, overrides
                    )
                    await session.commit()

                assert agent_def is not None, "instantiate_template returned None"

                # Check initial_balance
                if overrides.initial_balance is not None:
                    assert float(agent_def.initial_balance) == float(overrides.initial_balance), (
                        f"Expected overridden initial_balance={overrides.initial_balance}, "
                        f"got {agent_def.initial_balance}"
                    )

                # Check capabilities
                if overrides.capabilities is not None:
                    actual_caps = (
                        agent_def.capabilities.split(",")
                        if agent_def.capabilities
                        else []
                    )
                    # Filter out empty strings from split
                    actual_caps = [c for c in actual_caps if c]
                    assert sorted(actual_caps) == sorted(overrides.capabilities), (
                        f"Expected overridden capabilities={sorted(overrides.capabilities)}, "
                        f"got {sorted(actual_caps)}"
                    )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())

    @given(
        template_data=template_for_instantiation_st(),
        overrides=instantiate_override_st(),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_non_overridden_fields_use_template_defaults(
        self, template_data: dict, overrides: InstantiateRequest
    ) -> None:
        """When overrides are None, the AgentDefinition uses the template's default values.

        **Validates: Requirements 6.4**
        """

        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    author_id = await seed_author(session)
                    workspace_id = await seed_workspace(session, author_id)

                    template = AgentTemplate(
                        id=str(uuid.uuid4()),
                        name=template_data["name"],
                        description=template_data["description"],
                        agent_role=template_data["agent_role"],
                        capabilities_json=json.dumps(template_data["capabilities"]),
                        default_initial_balance=template_data["default_initial_balance"],
                        config_json=json.dumps(template_data["config"]),
                        author_id=author_id,
                        usage_count=0,
                    )
                    session.add(template)
                    await session.commit()

                    template_id = template.id

                async with session_factory() as session:
                    agent_def = await instantiate_template(
                        session, template_id, workspace_id, overrides
                    )
                    await session.commit()

                assert agent_def is not None, "instantiate_template returned None"

                # Check initial_balance falls back to template default
                if overrides.initial_balance is None:
                    assert float(agent_def.initial_balance) == float(
                        template_data["default_initial_balance"]
                    ), (
                        f"Expected default initial_balance="
                        f"{template_data['default_initial_balance']}, "
                        f"got {agent_def.initial_balance}"
                    )

                # Check capabilities falls back to template default
                if overrides.capabilities is None:
                    actual_caps = (
                        agent_def.capabilities.split(",")
                        if agent_def.capabilities
                        else []
                    )
                    actual_caps = [c for c in actual_caps if c]
                    assert sorted(actual_caps) == sorted(template_data["capabilities"]), (
                        f"Expected default capabilities="
                        f"{sorted(template_data['capabilities'])}, "
                        f"got {sorted(actual_caps)}"
                    )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())

    @given(
        template_data=template_for_instantiation_st(),
        overrides=instantiate_override_st(),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_agent_role_always_from_template(
        self, template_data: dict, overrides: InstantiateRequest
    ) -> None:
        """The agent_role always comes from the template (not overridable).

        **Validates: Requirements 6.4**
        """

        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    author_id = await seed_author(session)
                    workspace_id = await seed_workspace(session, author_id)

                    template = AgentTemplate(
                        id=str(uuid.uuid4()),
                        name=template_data["name"],
                        description=template_data["description"],
                        agent_role=template_data["agent_role"],
                        capabilities_json=json.dumps(template_data["capabilities"]),
                        default_initial_balance=template_data["default_initial_balance"],
                        config_json=json.dumps(template_data["config"]),
                        author_id=author_id,
                        usage_count=0,
                    )
                    session.add(template)
                    await session.commit()

                    template_id = template.id

                async with session_factory() as session:
                    agent_def = await instantiate_template(
                        session, template_id, workspace_id, overrides
                    )
                    await session.commit()

                assert agent_def is not None, "instantiate_template returned None"

                # agent_role must always match the template
                assert agent_def.agent_role == template_data["agent_role"], (
                    f"Expected agent_role='{template_data['agent_role']}', "
                    f"got '{agent_def.agent_role}'"
                )
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())


# ---------------------------------------------------------------------------
# Strategies for Property 11 — Template name validation
# ---------------------------------------------------------------------------

# Strings of valid length (3-100 chars) — printable characters
valid_name_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs", "P")),
    min_size=3,
    max_size=100,
)

# Strings that are too short (0-2 chars)
too_short_name_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs")),
    min_size=0,
    max_size=2,
)

# Strings that are too long (101+ chars)
too_long_name_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=101,
    max_size=300,
)


# ---------------------------------------------------------------------------
# Property 11 — Template name validation
# ---------------------------------------------------------------------------

class TestTemplateNameValidation:
    """Property 11: Template name validation.

    *For any* string, template name validation SHALL accept the string if and
    only if its length is between 3 and 100 characters inclusive. Duplicate
    names SHALL be rejected.

    **Validates: Requirements 6.6**
    """

    @given(name=valid_name_st)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_valid_length_names_accepted(self, name: str) -> None:
        """Names with length 3-100 are accepted by TemplateCreate.

        **Validates: Requirements 6.6**
        """
        from mesh_platform.schemas.marketplace import TemplateCreate

        assert 3 <= len(name) <= 100, f"Strategy produced invalid length: {len(name)}"

        # Should not raise — valid name
        template = TemplateCreate(
            name=name,
            agent_role="buyer",
        )
        assert template.name == name

    @given(name=too_short_name_st)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_too_short_names_rejected(self, name: str) -> None:
        """Names with length < 3 are rejected by TemplateCreate.

        **Validates: Requirements 6.6**
        """
        from pydantic import ValidationError
        from mesh_platform.schemas.marketplace import TemplateCreate

        assert len(name) < 3, f"Strategy produced valid length: {len(name)}"

        try:
            TemplateCreate(name=name, agent_role="buyer")
            raise AssertionError(
                f"TemplateCreate accepted name of length {len(name)}: {name!r}"
            )
        except ValidationError:
            pass  # Expected — name too short

    @given(name=too_long_name_st)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_too_long_names_rejected(self, name: str) -> None:
        """Names with length > 100 are rejected by TemplateCreate.

        **Validates: Requirements 6.6**
        """
        from pydantic import ValidationError
        from mesh_platform.schemas.marketplace import TemplateCreate

        assert len(name) > 100, f"Strategy produced valid length: {len(name)}"

        try:
            TemplateCreate(name=name, agent_role="buyer")
            raise AssertionError(
                f"TemplateCreate accepted name of length {len(name)}"
            )
        except ValidationError:
            pass  # Expected — name too long

    @given(name=valid_name_st)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_duplicate_names_rejected_at_db_level(self, name: str) -> None:
        """Inserting two templates with the same name raises IntegrityError.

        **Validates: Requirements 6.6**
        """
        from sqlalchemy.exc import IntegrityError

        async def _run():
            engine, session_factory = await create_test_db()
            try:
                async with session_factory() as session:
                    author_id = await seed_author(session)

                    # Insert first template — should succeed
                    session.add(AgentTemplate(
                        id=str(uuid.uuid4()),
                        name=name,
                        description=None,
                        agent_role="buyer",
                        capabilities_json="[]",
                        default_initial_balance=0.0,
                        config_json="{}",
                        author_id=author_id,
                        usage_count=0,
                    ))
                    await session.flush()

                    # Insert second template with same name — should fail
                    session.add(AgentTemplate(
                        id=str(uuid.uuid4()),
                        name=name,
                        description=None,
                        agent_role="supplier",
                        capabilities_json="[]",
                        default_initial_balance=0.0,
                        config_json="{}",
                        author_id=author_id,
                        usage_count=0,
                    ))
                    try:
                        await session.flush()
                        raise AssertionError(
                            f"DB accepted duplicate template name: {name!r}"
                        )
                    except IntegrityError:
                        pass  # Expected — unique constraint violation
            finally:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await engine.dispose()

        run_async(_run())
