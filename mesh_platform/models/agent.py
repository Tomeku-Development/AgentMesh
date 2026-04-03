"""Agent definition and status log ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mesh_platform.models.base import Base


class AgentDefinition(Base):
    __tablename__ = "agent_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    agent_role: Mapped[str] = mapped_column(String(30), nullable=False)
    agent_mesh_id: Mapped[str] = mapped_column(String(16), nullable=False)
    capabilities: Mapped[str] = mapped_column(Text, default="")
    initial_balance: Mapped[float] = mapped_column(Numeric(14, 2), default=10000)
    identity_seed_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentStatusLog(Base):
    __tablename__ = "agent_status_log"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    agent_definition_id: Mapped[str] = mapped_column(ForeignKey("agent_definitions.id", ondelete="CASCADE"), index=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    load: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    active_orders: Mapped[int] = mapped_column(Integer, default=0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
