"""Cost & Budgeting: media_generations, budgets, budget_reservations

Revision ID: 011
Revises: 010
Create Date: 2026-06-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
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
    op.create_table(
        "media_generations",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("episode_id", _uid(), nullable=False, index=True),
        sa.Column("shot_id", _uid(), nullable=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model", sa.String(120), nullable=True),
        sa.Column("units", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unit_cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(12), nullable=False, server_default="ok"),
        *_ts(),
    )
    op.create_table(
        "budgets",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("scope", sa.String(10), nullable=False, index=True),
        sa.Column("scope_id", _uid(), nullable=False, index=True),
        sa.Column("limit_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("soft_pct", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("hard_behavior", sa.String(10), nullable=False, server_default="block"),
        sa.Column("spent_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reserved_usd", sa.Float(), nullable=False, server_default="0"),
        sa.UniqueConstraint("scope", "scope_id", name="uq_budget_scope"),
        *_ts(),
    )
    op.create_table(
        "budget_reservations",
        sa.Column("id", _uid(), primary_key=True),
        sa.Column("budget_id", _uid(), sa.ForeignKey("budgets.id"), nullable=False, index=True),
        sa.Column("amount_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("job_id", sa.String(120), nullable=True, index=True),
        sa.Column("status", sa.String(12), nullable=False, server_default="active"),
        sa.Column("committed_usd", sa.Float(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True, index=True),
        *_ts(),
    )


def downgrade() -> None:
    op.drop_table("budget_reservations")
    op.drop_table("budgets")
    op.drop_table("media_generations")
