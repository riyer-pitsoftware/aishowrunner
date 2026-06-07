"""Showrunner: skill ledger + Series Brain (skill_invocations, series, canon,
episodes, shots, room artifacts)

Revision ID: 010
Revises: 009
Create Date: 2026-06-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uid():
    return pg.UUID(as_uuid=True)


def _ts():
    now = sa.func.now()
    dt = sa.DateTime(timezone=True)
    return (
        sa.Column("created_at", dt, server_default=now, nullable=False),
        sa.Column("updated_at", dt, server_default=now, nullable=False),
    )


def upgrade() -> None:
    # ── Sprint 2: skill invocation ledger ────────────────────────────────────
    op.create_table(
        "skill_invocations",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("series_id", _uid(), nullable=True, index=True),
        sa.Column("episode_id", _uid(), nullable=True, index=True),
        sa.Column("decision_id", sa.String(100), nullable=True),
        sa.Column("room", sa.String(40), nullable=True),
        sa.Column("gate", sa.String(40), nullable=True),
        sa.Column("skill_name", sa.String(80), nullable=False, index=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False, index=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cached_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "tokens_estimated", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cost_confidence", sa.String(12), nullable=False, server_default="exact"),
        sa.Column("status", sa.String(12), nullable=False, server_default="ok"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("stance", sa.String(12), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_output", sa.Text(), nullable=True),
        *_ts(),
    )

    # ── Sprint 3: Series Brain ───────────────────────────────────────────────
    op.create_table(
        "series",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False, index=True),
        sa.Column("premise", sa.Text(), nullable=True),
        sa.Column("era", sa.String(200), nullable=True),
        sa.Column("creative_rules", pg.JSONB(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        *_ts(),
    )
    op.create_table(
        "characters",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("series_id", _uid(), sa.ForeignKey("series.id"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False, index=True),
        sa.Column("slug", sa.String(200), nullable=False, index=True),
        sa.Column("role", sa.String(120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("attributes", pg.JSONB(), nullable=True),
        *_ts(),
    )
    op.create_table(
        "relationships",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("series_id", _uid(), sa.ForeignKey("series.id"), nullable=False, index=True),
        sa.Column("from_character_id", _uid(), nullable=False),
        sa.Column("to_character_id", _uid(), nullable=False),
        sa.Column("kind", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        *_ts(),
    )
    op.create_table(
        "canon_facts",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("series_id", _uid(), sa.ForeignKey("series.id"), nullable=False, index=True),
        sa.Column("fact_key", sa.String(200), nullable=False, index=True),
        sa.Column("category", sa.String(80), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("origin_episode_id", _uid(), nullable=True),
        sa.Column("provenance", pg.JSONB(), nullable=True),
        *_ts(),
    )
    op.create_table(
        "story_threads",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("series_id", _uid(), sa.ForeignKey("series.id"), nullable=False, index=True),
        sa.Column("thread_key", sa.String(200), nullable=False, index=True),
        sa.Column("title", sa.String(400), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("opened_episode_id", _uid(), nullable=True),
        sa.Column("resolved_episode_id", _uid(), nullable=True),
        *_ts(),
    )
    op.create_table(
        "canon_mutations",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("series_id", _uid(), sa.ForeignKey("series.id"), nullable=False, index=True),
        sa.Column("episode_id", _uid(), nullable=True, index=True),
        sa.Column("choice_id", _uid(), nullable=True),
        sa.Column("seq", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mutation_type", sa.String(40), nullable=False),
        sa.Column("target_type", sa.String(40), nullable=True),
        sa.Column("target_key", sa.String(200), nullable=True),
        sa.Column("payload", pg.JSONB(), nullable=True),
        sa.Column("provenance", pg.JSONB(), nullable=True),
        sa.Column("source_skill", sa.String(80), nullable=True),
        sa.Column("committed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_ts(),
    )

    # ── Episodes / production ────────────────────────────────────────────────
    op.create_table(
        "episodes",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("series_id", _uid(), sa.ForeignKey("series.id"), nullable=False, index=True),
        sa.Column("number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("title", sa.String(400), nullable=True),
        sa.Column("premise", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft", index=True),
        sa.Column("active_room", sa.String(40), nullable=True),
        sa.Column("beat_sheet", pg.JSONB(), nullable=True),
        *_ts(),
    )
    op.create_table(
        "branch_proposals",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("episode_id", _uid(), sa.ForeignKey("episodes.id"), nullable=False, index=True),
        sa.Column("title", sa.String(400), nullable=False),
        sa.Column("hook", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("payload", pg.JSONB(), nullable=True),
        sa.Column("selected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        *_ts(),
    )
    op.create_table(
        "beats",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("episode_id", _uid(), sa.ForeignKey("episodes.id"), nullable=False, index=True),
        sa.Column("index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("payload", pg.JSONB(), nullable=True),
        *_ts(),
    )
    op.create_table(
        "audience_choices",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("episode_id", _uid(), sa.ForeignKey("episodes.id"), nullable=False, index=True),
        sa.Column("label", sa.String(400), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("consequences", pg.JSONB(), nullable=True),
        sa.Column("selected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
    )
    op.create_table(
        "shots",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("episode_id", _uid(), sa.ForeignKey("episodes.id"), nullable=False, index=True),
        sa.Column("index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("inputs", pg.JSONB(), nullable=True),
        sa.Column("depends_on", pg.ARRAY(_uid()), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("artifact_id", _uid(), nullable=True),
        *_ts(),
    )
    op.create_table(
        "production_artifacts",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("episode_id", _uid(), sa.ForeignKey("episodes.id"), nullable=False, index=True),
        sa.Column("shot_id", _uid(), nullable=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("url", sa.String(800), nullable=True),
        sa.Column("mime_type", sa.String(80), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", pg.JSONB(), nullable=True),
        *_ts(),
    )

    # ── Room artifacts ───────────────────────────────────────────────────────
    op.create_table(
        "skill_contributions",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("episode_id", _uid(), sa.ForeignKey("episodes.id"), nullable=False, index=True),
        sa.Column("invocation_id", _uid(), sa.ForeignKey("skill_invocations.id"), nullable=True),
        sa.Column("room", sa.String(40), nullable=False, index=True),
        sa.Column("skill_name", sa.String(80), nullable=False, index=True),
        sa.Column("decision_id", sa.String(100), nullable=True, index=True),
        sa.Column("stance", sa.String(12), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("recommendations", pg.JSONB(), nullable=True),
        sa.Column("risks", pg.JSONB(), nullable=True),
        sa.Column("fields", pg.JSONB(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        *_ts(),
    )
    op.create_table(
        "specialist_disagreements",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("episode_id", _uid(), sa.ForeignKey("episodes.id"), nullable=False, index=True),
        sa.Column("decision_id", sa.String(100), nullable=True, index=True),
        sa.Column("axis", sa.String(120), nullable=False),
        sa.Column("stances", pg.JSONB(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        *_ts(),
    )
    op.create_table(
        "approval_gates",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("episode_id", _uid(), sa.ForeignKey("episodes.id"), nullable=False, index=True),
        sa.Column("gate", sa.String(20), nullable=False),
        sa.Column("verdict", sa.String(20), nullable=False),
        sa.Column("actor", sa.String(120), nullable=True),
        sa.Column("decision_id", sa.String(100), nullable=True),
        sa.Column("chosen_option_id", _uid(), nullable=True),
        sa.Column("dissent_snapshot", pg.JSONB(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        *_ts(),
    )


def downgrade() -> None:
    for table in (
        "approval_gates", "specialist_disagreements", "skill_contributions",
        "production_artifacts", "shots", "audience_choices", "beats",
        "branch_proposals", "episodes", "canon_mutations", "story_threads",
        "canon_facts", "relationships", "characters", "series", "skill_invocations",
    ):
        op.drop_table(table)
