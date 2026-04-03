"""Order and OrderEvent ORM models (event-sourced)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mesh_platform.models.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    goods: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    max_price_per_unit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    current_status: Mapped[str] = mapped_column(String(30), default="requested")
    winner_supplier_id: Mapped[str | None] = mapped_column(String(16), nullable=True)
    agreed_price_per_unit: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    bid_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    events: Mapped[list[OrderEvent]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderEvent(Base):
    __tablename__ = "order_events"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(16), nullable=False)
    payload_json: Mapped[str | None] = mapped_column(Text, default="{}")
    mqtt_message_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped[Order] = relationship(back_populates="events")
