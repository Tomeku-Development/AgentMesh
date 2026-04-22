"""Workspace and membership ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mesh_platform.models.base import Base


class WorkspaceRole(str, PyEnum):
    owner = "owner"
    admin = "admin"
    operator = "operator"
    developer = "developer"
    auditor = "auditor"
    viewer = "viewer"


ROLE_LEVELS: dict[str, int] = {
    WorkspaceRole.owner: 6,
    WorkspaceRole.admin: 5,
    WorkspaceRole.operator: 4,
    WorkspaceRole.developer: 3,
    WorkspaceRole.auditor: 2,
    WorkspaceRole.viewer: 1,
}


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    plan: Mapped[str] = mapped_column(String(20), default="starter")
    max_agents: Mapped[int] = mapped_column(Integer, default=10)
    config_json: Mapped[str | None] = mapped_column(Text, default="{}")
    credits_balance: Mapped[float] = mapped_column(Float, default=0.0)
    credits_used_this_month: Mapped[float] = mapped_column(Float, default=0.0)
    billing_cycle_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship("User")  # noqa: F821
    memberships: Mapped[list[WorkspaceMembership]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )


class WorkspaceMembership(Base):
    __tablename__ = "workspace_memberships"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_ws_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20), default=WorkspaceRole.viewer.value)

    workspace: Mapped[Workspace] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship("User")  # noqa: F821
