"""Reputation ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mesh_platform.models.base import Base


class ReputationEvent(Base):
    __tablename__ = "reputation_events"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    capability: Mapped[str] = mapped_column(String(50), nullable=False)
    old_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    new_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_order_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReputationSnapshot(Base):
    __tablename__ = "reputation_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    agent_id: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    capability: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), default=0.0)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
