"""Scenario service — CRUD operations for custom supply chain scenarios."""

from __future__ import annotations

import importlib
import inspect
import json
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mesh_platform.models.scenario import Scenario
from mesh_platform.schemas.scenario import (
    ScenarioCreate,
    ScenarioDefinition,
    ScenarioResponse,
    ScenarioUpdate,
)


def _serialize_definition(definition: ScenarioDefinition) -> str:
    """Serialize a ScenarioDefinition to a JSON string."""
    return json.dumps(definition.model_dump())


def _deserialize_definition(json_str: str) -> ScenarioDefinition:
    """Deserialize a JSON string back to a ScenarioDefinition."""
    return ScenarioDefinition.model_validate(json.loads(json_str))


def _scenario_to_response(scenario: Scenario) -> ScenarioResponse:
    """Convert a Scenario ORM model to a ScenarioResponse, deserializing the definition."""
    return ScenarioResponse(
        id=scenario.id,
        workspace_id=scenario.workspace_id,
        name=scenario.name,
        description=scenario.description,
        duration_seconds=scenario.duration_seconds,
        definition=_deserialize_definition(scenario.definition_json),
        is_system=scenario.is_system,
        created_at=scenario.created_at,
        updated_at=scenario.updated_at,
    )


async def create_scenario(
    db: AsyncSession,
    workspace_id: str,
    data: ScenarioCreate,
) -> ScenarioResponse:
    """Create a new custom scenario in the workspace."""
    scenario = Scenario(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        name=data.name,
        description=data.description,
        duration_seconds=data.duration_seconds,
        definition_json=_serialize_definition(data.definition),
        is_system=False,
    )
    db.add(scenario)
    await db.flush()
    return _scenario_to_response(scenario)


async def list_scenarios(
    db: AsyncSession,
    workspace_id: str,
) -> list[ScenarioResponse]:
    """List all workspace scenarios plus built-in system scenarios."""
    # Query workspace scenarios from DB
    result = await db.execute(
        select(Scenario).where(Scenario.workspace_id == workspace_id)
    )
    db_scenarios = [_scenario_to_response(s) for s in result.scalars().all()]

    # Append built-in system scenarios
    system_scenarios = _load_builtin_scenarios(workspace_id)

    return db_scenarios + system_scenarios


async def get_scenario(
    db: AsyncSession,
    scenario_id: str,
) -> ScenarioResponse | None:
    """Get a single scenario by ID, deserializing its definition."""
    result = await db.execute(
        select(Scenario).where(Scenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()
    if scenario is None:
        return None
    return _scenario_to_response(scenario)


async def update_scenario(
    db: AsyncSession,
    scenario_id: str,
    data: ScenarioUpdate,
) -> ScenarioResponse | None:
    """Update an existing scenario's fields. Re-serializes definition if changed."""
    result = await db.execute(
        select(Scenario).where(Scenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()
    if scenario is None:
        return None

    if data.name is not None:
        scenario.name = data.name
    if data.description is not None:
        scenario.description = data.description
    if data.duration_seconds is not None:
        scenario.duration_seconds = data.duration_seconds
    if data.definition is not None:
        scenario.definition_json = _serialize_definition(data.definition)

    scenario.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return _scenario_to_response(scenario)


async def delete_scenario(
    db: AsyncSession,
    scenario_id: str,
) -> bool:
    """Delete a scenario by ID. Returns True if deleted, False if not found."""
    result = await db.execute(
        select(Scenario).where(Scenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()
    if scenario is None:
        return False
    await db.delete(scenario)
    await db.flush()
    return True


def _load_builtin_scenarios(workspace_id: str) -> list[ScenarioResponse]:
    """Load built-in system scenarios from the mesh/scenarios/ directory.

    Discovers all BaseScenario subclasses in the mesh.scenarios package and
    converts them to ScenarioResponse objects with is_system=True.
    Returns an empty list if the directory doesn't exist or has no valid scenarios.
    """
    scenarios: list[ScenarioResponse] = []

    try:
        scenarios_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "mesh",
            "scenarios",
        )
        if not os.path.isdir(scenarios_dir):
            return []

        # Lazy import to avoid hard dependency on mesh package at module level
        from mesh.scenarios.base import BaseScenario

        # Scan for Python modules in the scenarios directory
        for filename in sorted(os.listdir(scenarios_dir)):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            module_name = f"mesh.scenarios.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
            except Exception:
                continue

            # Find all BaseScenario subclasses in the module
            for _name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, BaseScenario)
                    and obj is not BaseScenario
                ):
                    try:
                        instance = obj()
                        scenario_resp = _builtin_to_response(instance, workspace_id)
                        scenarios.append(scenario_resp)
                    except Exception:
                        continue
    except Exception:
        return []

    return scenarios


def _builtin_to_response(
    scenario: object,
    workspace_id: str,
) -> ScenarioResponse:
    """Convert a built-in BaseScenario instance to a ScenarioResponse."""
    from mesh.scenarios.base import BaseScenario

    assert isinstance(scenario, BaseScenario)

    # Convert agents
    agents = []
    for a in scenario.agents:
        agents.append({
            "role": a.role,
            "count": a.count,
            "initial_balance": a.initial_balance,
            "capabilities": list(a.capabilities),
        })

    # Convert goods
    goods = []
    for g in scenario.goods:
        goods.append({
            "name": g.name,
            "category": g.category,
            "base_price": g.base_price,
            "volatility": g.volatility,
        })

    # Convert orders
    orders = []
    for o in scenario.orders:
        orders.append({
            "at_second": int(o.at_second),
            "goods": o.goods,
            "category": o.category,
            "quantity": o.quantity,
            "max_price_per_unit": o.max_price_per_unit,
            "quality_threshold": o.quality_threshold,
        })

    # Convert chaos events
    chaos_events = []
    for c in scenario.chaos_events:
        chaos_events.append({
            "at_second": int(c.at_second),
            "event_type": c.event_type,
            "target": c.target,
        })

    definition = ScenarioDefinition.model_validate({
        "agents": agents,
        "goods": goods,
        "orders": orders,
        "chaos_events": chaos_events,
    })

    # Use a deterministic ID based on the scenario name
    deterministic_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"mesh.builtin.{scenario.name}"))
    now = datetime.now(timezone.utc)

    return ScenarioResponse(
        id=deterministic_id,
        workspace_id=workspace_id,
        name=scenario.name,
        description=scenario.description,
        duration_seconds=scenario.duration_seconds,
        definition=definition,
        is_system=True,
        created_at=now,
        updated_at=None,
    )
