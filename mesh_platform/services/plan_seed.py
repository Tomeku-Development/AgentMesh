"""Subscription plan seed data for system initialization."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from mesh_platform.models.usage import SubscriptionPlan


PLAN_SEEDS = [
    {
        "name": "starter",
        "display_name": "Starter",
        "description": "Free tier for experimentation and small projects. Perfect for getting started with MESH agent orchestration.",
        "monthly_price": 0.0,
        "monthly_credits": 1000,
        "max_agents": 5,
        "max_workspaces": 3,
        "max_api_keys": 5,
        "llm_requests_per_day": 100,
        "llm_tokens_per_month": 100000,
        "features_json": {
            "basic_analytics": True,
            "community_support": True,
            "priority_support": False,
            "custom_models": False,
            "sla_guarantee": False,
            "api_access": True,
            "webhook_integrations": False,
            "custom_capabilities": False,
            "export_data": False,
            "team_members": 1,
        },
        "sort_order": 0,
    },
    {
        "name": "pro",
        "display_name": "Pro",
        "description": "For growing teams and production workloads. Full analytics, priority support, and expanded limits.",
        "monthly_price": 49.0,
        "monthly_credits": 25000,
        "max_agents": 25,
        "max_workspaces": 10,
        "max_api_keys": 25,
        "llm_requests_per_day": 2500,
        "llm_tokens_per_month": 2500000,
        "features_json": {
            "basic_analytics": True,
            "full_analytics": True,
            "community_support": True,
            "priority_support": True,
            "custom_models": False,
            "sla_guarantee": False,
            "api_access": True,
            "webhook_integrations": True,
            "custom_capabilities": True,
            "export_data": True,
            "team_members": 5,
        },
        "sort_order": 1,
    },
    {
        "name": "enterprise",
        "display_name": "Enterprise",
        "description": "For large-scale deployments with custom SLAs. Dedicated support, custom models, and unlimited capabilities.",
        "monthly_price": 199.0,
        "monthly_credits": 150000,
        "max_agents": 100,
        "max_workspaces": 50,
        "max_api_keys": 100,
        "llm_requests_per_day": 25000,
        "llm_tokens_per_month": 25000000,
        "features_json": {
            "basic_analytics": True,
            "full_analytics": True,
            "advanced_analytics": True,
            "community_support": True,
            "priority_support": True,
            "dedicated_support": True,
            "custom_models": True,
            "sla_guarantee": True,
            "api_access": True,
            "webhook_integrations": True,
            "custom_capabilities": True,
            "export_data": True,
            "team_members": 25,
        },
        "sort_order": 2,
    },
    {
        "name": "custom",
        "display_name": "Custom",
        "description": "Tailored plan for unique requirements. Contact us for custom pricing, limits, and dedicated infrastructure.",
        "monthly_price": 0.0,  # Negotiable
        "monthly_credits": 500000,
        "max_agents": 500,
        "max_workspaces": 200,
        "max_api_keys": 500,
        "llm_requests_per_day": 100000,
        "llm_tokens_per_month": 100000000,
        "features_json": {
            "basic_analytics": True,
            "full_analytics": True,
            "advanced_analytics": True,
            "community_support": True,
            "priority_support": True,
            "dedicated_support": True,
            "custom_models": True,
            "sla_guarantee": True,
            "api_access": True,
            "webhook_integrations": True,
            "custom_capabilities": True,
            "export_data": True,
            "dedicated_infrastructure": True,
            "team_members": -1,  # unlimited
        },
        "sort_order": 3,
    },
]


async def seed_plans(db: AsyncSession) -> None:
    """Seed subscription plans if they don't already exist.
    
    This function is idempotent - it checks for existing plans by name
    before inserting new ones.
    """
    for plan_data in PLAN_SEEDS:
        # Check if plan already exists by name
        result = await db.execute(
            select(SubscriptionPlan).where(
                SubscriptionPlan.name == plan_data["name"],
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing is None:
            plan = SubscriptionPlan(
                name=plan_data["name"],
                display_name=plan_data["display_name"],
                description=plan_data["description"],
                monthly_price=plan_data["monthly_price"],
                monthly_credits=plan_data["monthly_credits"],
                max_agents=plan_data["max_agents"],
                max_workspaces=plan_data["max_workspaces"],
                max_api_keys=plan_data["max_api_keys"],
                llm_requests_per_day=plan_data["llm_requests_per_day"],
                llm_tokens_per_month=plan_data["llm_tokens_per_month"],
                features_json=plan_data["features_json"],
                sort_order=plan_data["sort_order"],
            )
            db.add(plan)
