"""Episodes, branches, beats, choices, shots, artifacts (TRD §8, §9)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from chronocanvas.db.base import Base, TimestampMixin, UUIDMixin


class Episode(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "episodes"

    series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("series.id"), index=True
    )
    number: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str | None] = mapped_column(String(400))
    premise: Mapped[str | None] = mapped_column(Text)
    # Lifecycle (chronocanvas.showrunner.episodes.state.EpisodeStatus)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    active_room: Mapped[str | None] = mapped_column(String(40))
    beat_sheet: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class BranchProposal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "branch_proposals"

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("episodes.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(400))
    hook: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    # payload: consequences, threads, complexity
    payload: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)


class Beat(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "beats"

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("episodes.id"), index=True
    )
    index: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class AudienceChoice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audience_choices"

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("episodes.id"), index=True
    )
    label: Mapped[str] = mapped_column(String(400))
    description: Mapped[str | None] = mapped_column(Text)
    consequences: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    selected_at: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True))


class Shot(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "shots"

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("episodes.id"), index=True
    )
    index: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text)
    inputs: Mapped[dict | None] = mapped_column(JSONB, default=dict)  # prompt, style refs, reuse
    depends_on: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list
    )
    # pending|generating|ready|stale|approved (TRD §9.3)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    artifact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class ProductionArtifact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "production_artifacts"

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("episodes.id"), index=True
    )
    shot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    kind: Mapped[str] = mapped_column(String(20))  # image|audio|video|episode
    url: Mapped[str | None] = mapped_column(String(800))
    mime_type: Mapped[str | None] = mapped_column(String(80))
    version: Mapped[int] = mapped_column(Integer, default=1)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    payload: Mapped[dict | None] = mapped_column(JSONB, default=dict)
