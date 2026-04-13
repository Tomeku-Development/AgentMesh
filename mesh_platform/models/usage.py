"""LLM usage tracking and subscription plan models."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, JSON
from mesh_platform.models.base import Base


class LLMUsageEvent(Base):
    __tablename__ = "llm_usage_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True)  # may be system-triggered
    agent_id = Column(String, nullable=True)
    agent_role = Column(String(50), nullable=True)  # buyer, supplier, etc.
    model = Column(String(200), nullable=False)  # e.g. "anthropic.claude-3-sonnet"
    provider = Column(String(50), nullable=False)  # "bedrock" or "openrouter"
    prompt_type = Column(String(100), nullable=True)  # "supplier_bid", "inspector_quality", etc.
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)  # USD
    credits_charged = Column(Float, default=0.0)  # Credits deducted
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True)  # "starter", "pro", "enterprise", "custom"
    display_name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    monthly_price = Column(Float, default=0.0)  # USD
    monthly_credits = Column(Integer, default=1000)
    max_agents = Column(Integer, default=5)
    max_workspaces = Column(Integer, default=3)
    max_api_keys = Column(Integer, default=5)
    llm_requests_per_day = Column(Integer, default=100)
    llm_tokens_per_month = Column(Integer, default=100000)
    features_json = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
