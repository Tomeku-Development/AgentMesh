"""Marketplace service — CRUD and instantiation for agent templates."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.models.agent import AgentDefinition
from mesh_platform.models.marketplace import AgentTemplate
from mesh_platform.schemas.marketplace import (
    InstantiateRequest,
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
)


def _template_to_response(template: AgentTemplate) -> TemplateResponse:
    """Convert an AgentTemplate ORM model to a TemplateResponse, deserializing JSON fields."""
    return TemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        agent_role=template.agent_role,
        capabilities=json.loads(template.capabilities_json),
        default_initial_balance=template.default_initial_balance,
        config=json.loads(template.config_json),
        author_id=template.author_id,
        usage_count=template.usage_count,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


async def register_template(
    db: AsyncSession,
    author_id: str,
    data: TemplateCreate,
) -> TemplateResponse:
    """Register a new agent template in the marketplace (Requirement 6.1)."""
    template = AgentTemplate(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        agent_role=data.agent_role,
        capabilities_json=json.dumps(data.capabilities),
        default_initial_balance=data.default_initial_balance,
        config_json=json.dumps(data.config),
        author_id=author_id,
        usage_count=0,
    )
    db.add(template)
    await db.flush()
    return _template_to_response(template)


async def search_templates(
    db: AsyncSession,
    q: str | None = None,
    role: str | None = None,
    capability: str | None = None,
) -> list[TemplateResponse]:
    """Search templates with text search, role filter, capability filter (Requirement 6.2).

    - ``q``: text search on name/description (LIKE)
    - ``role``: exact match on agent_role
    - ``capability``: checks if capability string is present in capabilities_json
    - Results ordered by usage_count DESC
    """
    stmt = select(AgentTemplate)

    if q is not None:
        pattern = f"%{q}%"
        stmt = stmt.where(
            AgentTemplate.name.ilike(pattern) | AgentTemplate.description.ilike(pattern)
        )

    if role is not None:
        stmt = stmt.where(AgentTemplate.agent_role == role)

    if capability is not None:
        # capabilities_json stores a JSON array, e.g. '["electronics", "food"]'
        # Use LIKE to check if the capability string appears in the JSON array
        stmt = stmt.where(AgentTemplate.capabilities_json.ilike(f'%"{capability}"%'))

    stmt = stmt.order_by(AgentTemplate.usage_count.desc())

    result = await db.execute(stmt)
    return [_template_to_response(t) for t in result.scalars().all()]


async def get_template(
    db: AsyncSession,
    template_id: str,
) -> TemplateResponse | None:
    """Get a single template by ID, deserializing JSON fields (Requirement 6.3)."""
    result = await db.execute(
        select(AgentTemplate).where(AgentTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if template is None:
        return None
    return _template_to_response(template)


async def update_template(
    db: AsyncSession,
    template_id: str,
    author_id: str,
    data: TemplateUpdate,
) -> TemplateResponse | None:
    """Update a template only if the requesting user is the author (Requirement 6.7).

    Returns None if the template is not found or the user is not the author.
    """
    result = await db.execute(
        select(AgentTemplate).where(AgentTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if template is None:
        return None
    if template.author_id != author_id:
        return None

    if data.name is not None:
        template.name = data.name
    if data.description is not None:
        template.description = data.description
    if data.agent_role is not None:
        template.agent_role = data.agent_role
    if data.capabilities is not None:
        template.capabilities_json = json.dumps(data.capabilities)
    if data.default_initial_balance is not None:
        template.default_initial_balance = data.default_initial_balance
    if data.config is not None:
        template.config_json = json.dumps(data.config)

    template.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return _template_to_response(template)


async def instantiate_template(
    db: AsyncSession,
    template_id: str,
    workspace_id: str,
    overrides: InstantiateRequest,
) -> AgentDefinition | None:
    """Instantiate a template into a workspace AgentDefinition (Requirement 6.4, 6.5).

    Creates an AgentDefinition using the template's defaults, applying any overrides
    from the request. Increments the template's usage_count.

    Returns None if the template is not found.
    """
    result = await db.execute(
        select(AgentTemplate).where(AgentTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if template is None:
        return None

    # Determine final values: use override if provided, otherwise template default
    initial_balance = (
        overrides.initial_balance
        if overrides.initial_balance is not None
        else template.default_initial_balance
    )
    capabilities = (
        overrides.capabilities
        if overrides.capabilities is not None
        else json.loads(template.capabilities_json)
    )

    # Generate a short mesh ID (8 hex chars from uuid4)
    agent_mesh_id = uuid.uuid4().hex[:16]

    agent_def = AgentDefinition(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        agent_role=template.agent_role,
        agent_mesh_id=agent_mesh_id,
        capabilities=",".join(capabilities),
        initial_balance=initial_balance,
        is_active=True,
    )
    db.add(agent_def)

    # Increment usage count
    template.usage_count = template.usage_count + 1
    await db.flush()

    return agent_def
