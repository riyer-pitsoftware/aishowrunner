"""Room artifacts — contributions, disagreements, approval gates (TRD §8).

Data layer only in Sprint 3; room behavior (fan-out, comparator, gate state
machine) lands in Sprint 4. ApprovalGate + selected AudienceChoice are guarded
against rewrite (dissent and decisions are immutable — TRD §8.3).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from chronocanvas.db.base import Base, TimestampMixin, UUIDMixin


class SkillContribution(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "skill_contributions"

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("episodes.id"), index=True
    )
    invocation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_invocations.id")
    )
    room: Mapped[str] = mapped_column(String(40), index=True)
    skill_name: Mapped[str] = mapped_column(String(80), index=True)
    decision_id: Mapped[str | None] = mapped_column(String(100), index=True)
    stance: Mapped[str | None] = mapped_column(String(12))
    summary: Mapped[str | None] = mapped_column(Text)
    recommendations: Mapped[dict | None] = mapped_column(JSONB, default=list)
    risks: Mapped[dict | None] = mapped_column(JSONB, default=list)
    fields: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    raw_text: Mapped[str | None] = mapped_column(Text)


class SpecialistDisagreement(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "specialist_disagreements"

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("episodes.id"), index=True
    )
    decision_id: Mapped[str | None] = mapped_column(String(100), index=True)
    axis: Mapped[str] = mapped_column(String(120))  # what they disagree about
    stances: Mapped[dict | None] = mapped_column(JSONB, default=dict)  # skill -> stance
    detail: Mapped[str | None] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)


class ApprovalGate(Base, UUIDMixin, TimestampMixin):
    """A greenlight decision. Immutable once recorded — preserves dissent (TRD §8.3)."""

    __tablename__ = "approval_gates"

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("episodes.id"), index=True
    )
    gate: Mapped[str] = mapped_column(String(20))  # branch|episode|final
    verdict: Mapped[str] = mapped_column(String(20))  # approved|defer|reduce|kill
    actor: Mapped[str | None] = mapped_column(String(120))
    decision_id: Mapped[str | None] = mapped_column(String(100))
    chosen_option_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    dissent_snapshot: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    rationale: Mapped[str | None] = mapped_column(Text)
