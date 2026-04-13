"""Capability registry model."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime
from mesh_platform.models.base import Base


class Capability(Base):
    __tablename__ = "capabilities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)  # normalized lowercase
    display_name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, index=True)  # domain, process, iot, logistics, quality, market
    description = Column(Text, nullable=False)  # Rich description for LLM context
    applicable_roles = Column(String(200), default="")  # comma-separated roles
    is_system = Column(Boolean, default=True)
    workspace_id = Column(String, nullable=True, index=True)  # null = global
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
