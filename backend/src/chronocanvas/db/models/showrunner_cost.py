"""Cost & Budgeting tables (TRD §6.3, §6.4) — media ledger + budgets + reservations.

(The skill ledger is ``skill_invocations`` from Sprint 2.)
"""

from __future__ import annotations

import uuid

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from chronocanvas.db.base import Base, TimestampMixin, UUIDMixin


class MediaGeneration(Base, UUIDMixin, TimestampMixin):
    """One row per image/video/tts/scene-edit job (TRD §6.3)."""

    __tablename__ = "media_generations"

    episode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    shot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    kind: Mapped[str] = mapped_column(String(20))  # image|video|tts|scene_edit
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str | None] = mapped_column(String(120))
    units: Mapped[float] = mapped_column(Float, default=0.0)  # images|seconds|1k-chars
    unit_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(12), default="ok")  # ok|failed


class Budget(Base, UUIDMixin, TimestampMixin):
    """A spend cap for a series or episode (TRD §6.4)."""

    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("scope", "scope_id", name="uq_budget_scope"),)

    scope: Mapped[str] = mapped_column(String(10), index=True)  # series|episode
    scope_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    limit_usd: Mapped[float] = mapped_column(Float, default=0.0)  # <=0 = uncapped
    soft_pct: Mapped[float] = mapped_column(Float, default=0.8)
    hard_behavior: Mapped[str] = mapped_column(String(10), default="block")  # block|warn
    spent_usd: Mapped[float] = mapped_column(Float, default=0.0)
    reserved_usd: Mapped[float] = mapped_column(Float, default=0.0)


class BudgetReservation(Base, UUIDMixin, TimestampMixin):
    """A pending reservation against a budget; TTL'd for crash safety (TRD §6.5)."""

    __tablename__ = "budget_reservations"

    budget_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("budgets.id"), index=True
    )
    amount_usd: Mapped[float] = mapped_column(Float, default=0.0)
    job_id: Mapped[str | None] = mapped_column(String(120), index=True)
    # status: active|committed|released|expired
    status: Mapped[str] = mapped_column(String(12), default="active")
    committed_usd: Mapped[float | None] = mapped_column(Float)
    expires_at: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True), index=True)
