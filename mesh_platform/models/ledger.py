"""LedgerEntry and EscrowRecord ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mesh_platform.models.base import Base


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    tx_id: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    tx_type: Mapped[str] = mapped_column(String(30), nullable=False)
    from_agent: Mapped[str] = mapped_column(String(16), nullable=False)
    to_agent: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    order_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    balance_after_from: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    balance_after_to: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EscrowRecord(Base):
    __tablename__ = "escrow_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    order_id: Mapped[str] = mapped_column(String(36), nullable=False)
    from_agent: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    released: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
