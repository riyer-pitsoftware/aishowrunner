"""skill_invocation — the priced, attributed skill-call ledger (TRD §5.4, §6.3).

One row per skill invocation. Cost columns are populated by the Cost & Budgeting
subsystem; this sprint records tokens, model/provider, content hash, attribution,
and the (optional) parsed stance/summary for fast disagreement/audit queries.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from chronocanvas.db.base import Base, TimestampMixin, UUIDMixin


class SkillInvocation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "skill_invocations"

    # Attribution (TRD §5.4)
    series_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    decision_id: Mapped[str | None] = mapped_column(String(100))
    room: Mapped[str | None] = mapped_column(String(40))
    gate: Mapped[str | None] = mapped_column(String(40))

    # Skill identity + resolved model
    skill_name: Mapped[str] = mapped_column(String(80), index=True)
    content_hash: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(120))
    provider: Mapped[str] = mapped_column(String(40), index=True)

    # Usage + cost (cost filled by Cost & Budgeting subsystem)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cached_tokens: Mapped[int] = mapped_column(Integer, default=0)
    tokens_estimated: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    cost_confidence: Mapped[str] = mapped_column(String(12), default="exact")  # exact|estimated

    # Outcome + (optional) parsed contribution summary
    status: Mapped[str] = mapped_column(String(12), default="ok")  # ok|failed
    error: Mapped[str | None] = mapped_column(Text)
    stance: Mapped[str | None] = mapped_column(String(12))
    summary: Mapped[str | None] = mapped_column(Text)
    raw_output: Mapped[str | None] = mapped_column(Text)
