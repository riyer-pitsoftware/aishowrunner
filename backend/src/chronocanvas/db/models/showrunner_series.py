"""Series Brain — series, characters, canon (TRD §10).

Canon's source of truth is the append-only ``CanonMutation`` log; ``CanonFact`` /
``StoryThread`` are materialized snapshots rebuilt by folding mutations
(chronocanvas.showrunner.canon). Mutations carry provenance and cannot be
rewritten (immutability guard).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from chronocanvas.db.base import Base, TimestampMixin, UUIDMixin


class Series(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "series"

    title: Mapped[str] = mapped_column(String(300), index=True)
    premise: Mapped[str | None] = mapped_column(Text)
    era: Mapped[str | None] = mapped_column(String(200))  # e.g. "Chola Tamil Nadu, 10th c."
    creative_rules: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|archived


class Character(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "characters"

    series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("series.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), index=True)
    slug: Mapped[str] = mapped_column(String(200), index=True)
    role: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    attributes: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class Relationship(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "relationships"

    series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("series.id"), index=True
    )
    from_character_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    to_character_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    kind: Mapped[str] = mapped_column(String(80))  # ally|rival|kin|patron|...
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")


class CanonFact(Base, UUIDMixin, TimestampMixin):
    """Materialized snapshot fact (rebuildable from CanonMutation)."""

    __tablename__ = "canon_facts"

    series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("series.id"), index=True
    )
    fact_key: Mapped[str] = mapped_column(String(200), index=True)
    category: Mapped[str | None] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|retired
    origin_episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    provenance: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class StoryThread(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "story_threads"

    series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("series.id"), index=True
    )
    thread_key: Mapped[str] = mapped_column(String(200), index=True)
    title: Mapped[str] = mapped_column(String(400))
    status: Mapped[str] = mapped_column(String(20), default="open")  # open|resolved
    opened_episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    resolved_episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class CanonMutation(Base, UUIDMixin, TimestampMixin):
    """Append-only canon change with provenance (TRD §10.2). Never updated/deleted."""

    __tablename__ = "canon_mutations"

    series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("series.id"), index=True
    )
    episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    choice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    seq: Mapped[int] = mapped_column(Integer, default=0)  # tie-breaker within a timestamp
    mutation_type: Mapped[str] = mapped_column(String(40))  # see canon.MutationType
    # target_type: fact|thread|character|relationship
    target_type: Mapped[str | None] = mapped_column(String(40))
    target_key: Mapped[str | None] = mapped_column(String(200))
    payload: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    provenance: Mapped[dict | None] = mapped_column(JSONB, default=dict)  # decision_id/gate/skill
    source_skill: Mapped[str | None] = mapped_column(String(80))
    committed: Mapped[bool] = mapped_column(Boolean, default=True)
