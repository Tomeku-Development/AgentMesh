"""Unit tests for the marketplace service (Requirement 6)."""

from __future__ import annotations

import json

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.models.marketplace import AgentTemplate
from mesh_platform.models.user import User
from mesh_platform.schemas.marketplace import (
    InstantiateRequest,
    TemplateCreate,
    TemplateUpdate,
)
from mesh_platform.services import marketplace_service


@pytest_asyncio.fixture
async def author(db_session: AsyncSession) -> User:
    """Create a test user to act as template author."""
    user = User(
        id="author-001",
        email="author@mesh.io",
        password_hash="hashed",
        display_name="Author",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def other_user(db_session: AsyncSession) -> User:
    """Create a second test user."""
    user = User(
        id="other-002",
        email="other@mesh.io",
        password_hash="hashed",
        display_name="Other",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def sample_template(db_session: AsyncSession, author: User) -> AgentTemplate:
    """Create a sample template directly in the DB for read/update tests."""
    template = AgentTemplate(
        id="tmpl-001",
        name="Test Buyer Template",
        description="A test buyer template",
        agent_role="buyer",
        capabilities_json=json.dumps(["electronics", "food"]),
        default_initial_balance=5000.0,
        config_json=json.dumps({"strategy": "aggressive"}),
        author_id=author.id,
        usage_count=10,
    )
    db_session.add(template)
    await db_session.flush()
    return template


# ── register_template ──


@pytest.mark.asyncio
async def test_register_template(db_session: AsyncSession, author: User):
    data = TemplateCreate(
        name="My Supplier",
        description="A supplier template",
        agent_role="supplier",
        capabilities=["metals", "plastics"],
        default_initial_balance=8000.0,
        config={"strategy": "conservative"},
    )
    resp = await marketplace_service.register_template(db_session, author.id, data)

    assert resp.name == "My Supplier"
    assert resp.agent_role == "supplier"
    assert resp.capabilities == ["metals", "plastics"]
    assert resp.default_initial_balance == 8000.0
    assert resp.config == {"strategy": "conservative"}
    assert resp.author_id == author.id
    assert resp.usage_count == 0
    assert resp.id is not None


# ── search_templates ──


@pytest.mark.asyncio
async def test_search_templates_no_filters(db_session: AsyncSession, sample_template):
    results = await marketplace_service.search_templates(db_session)
    assert len(results) == 1
    assert results[0].name == "Test Buyer Template"


@pytest.mark.asyncio
async def test_search_templates_text_query(db_session: AsyncSession, sample_template):
    results = await marketplace_service.search_templates(db_session, q="Buyer")
    assert len(results) == 1

    results = await marketplace_service.search_templates(db_session, q="nonexistent")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_templates_filter_by_role(db_session: AsyncSession, sample_template):
    results = await marketplace_service.search_templates(db_session, role="buyer")
    assert len(results) == 1

    results = await marketplace_service.search_templates(db_session, role="supplier")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_templates_filter_by_capability(
    db_session: AsyncSession, sample_template
):
    results = await marketplace_service.search_templates(db_session, capability="electronics")
    assert len(results) == 1

    results = await marketplace_service.search_templates(db_session, capability="metals")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_templates_ordered_by_usage_count(
    db_session: AsyncSession, author: User
):
    """Templates should be returned ordered by usage_count DESC."""
    for i, count in enumerate([5, 20, 1]):
        t = AgentTemplate(
            id=f"tmpl-order-{i}",
            name=f"Template {i}",
            description="desc",
            agent_role="buyer",
            capabilities_json="[]",
            default_initial_balance=1000.0,
            config_json="{}",
            author_id=author.id,
            usage_count=count,
        )
        db_session.add(t)
    await db_session.flush()

    results = await marketplace_service.search_templates(db_session)
    counts = [r.usage_count for r in results]
    assert counts == sorted(counts, reverse=True)


# ── get_template ──


@pytest.mark.asyncio
async def test_get_template_found(db_session: AsyncSession, sample_template):
    resp = await marketplace_service.get_template(db_session, "tmpl-001")
    assert resp is not None
    assert resp.name == "Test Buyer Template"
    assert resp.capabilities == ["electronics", "food"]
    assert resp.config == {"strategy": "aggressive"}


@pytest.mark.asyncio
async def test_get_template_not_found(db_session: AsyncSession):
    resp = await marketplace_service.get_template(db_session, "nonexistent")
    assert resp is None


# ── update_template ──


@pytest.mark.asyncio
async def test_update_template_by_author(db_session: AsyncSession, author, sample_template):
    data = TemplateUpdate(name="Updated Name", capabilities=["new_cap"])
    resp = await marketplace_service.update_template(
        db_session, "tmpl-001", author.id, data
    )
    assert resp is not None
    assert resp.name == "Updated Name"
    assert resp.capabilities == ["new_cap"]
    # Unchanged fields should remain
    assert resp.agent_role == "buyer"
    assert resp.updated_at is not None


@pytest.mark.asyncio
async def test_update_template_not_author(
    db_session: AsyncSession, other_user, sample_template
):
    data = TemplateUpdate(name="Hacked Name")
    resp = await marketplace_service.update_template(
        db_session, "tmpl-001", other_user.id, data
    )
    assert resp is None


@pytest.mark.asyncio
async def test_update_template_not_found(db_session: AsyncSession, author):
    data = TemplateUpdate(name="Ghost")
    resp = await marketplace_service.update_template(
        db_session, "nonexistent", author.id, data
    )
    assert resp is None


# ── instantiate_template ──


@pytest.mark.asyncio
async def test_instantiate_template_defaults(
    db_session: AsyncSession, sample_template
):
    overrides = InstantiateRequest()
    agent = await marketplace_service.instantiate_template(
        db_session, "tmpl-001", "ws-001", overrides
    )
    assert agent is not None
    assert agent.workspace_id == "ws-001"
    assert agent.agent_role == "buyer"
    assert agent.initial_balance == 5000.0
    assert "electronics" in agent.capabilities
    assert "food" in agent.capabilities
    assert agent.is_active is True

    # usage_count should have incremented
    updated = await marketplace_service.get_template(db_session, "tmpl-001")
    assert updated.usage_count == 11


@pytest.mark.asyncio
async def test_instantiate_template_with_overrides(
    db_session: AsyncSession, sample_template
):
    overrides = InstantiateRequest(
        initial_balance=9999.0,
        capabilities=["custom_cap"],
    )
    agent = await marketplace_service.instantiate_template(
        db_session, "tmpl-001", "ws-002", overrides
    )
    assert agent is not None
    assert agent.initial_balance == 9999.0
    assert agent.capabilities == "custom_cap"


@pytest.mark.asyncio
async def test_instantiate_template_not_found(db_session: AsyncSession):
    overrides = InstantiateRequest()
    agent = await marketplace_service.instantiate_template(
        db_session, "nonexistent", "ws-001", overrides
    )
    assert agent is None
