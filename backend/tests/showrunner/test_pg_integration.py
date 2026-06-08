"""Postgres integration test for the showrunner tables (bead asr-05c).

The rest of the suite runs on in-memory SQLite, which silently shims away the
Postgres-only column types the showrunner schema actually relies on:

    * JSONB              (Shot.inputs, ProductionArtifact.payload, SkillContribution.fields, ...)
    * ARRAY(UUID)        (Shot.depends_on — SQLite has no native array type at all)
    * UUID               (every primary/foreign key)

This test runs ``alembic upgrade head`` against a *real* Postgres and then does
CRUD through the async ORM, asserting those types round-trip with full fidelity.
It is GUARDED on an env var so the default `pytest` run (no Postgres server)
SKIPS cleanly instead of erroring — and so collection succeeds even when the
heavy drivers (asyncpg / alembic / psycopg) are not installed. All such imports
are performed lazily *inside* the test body, after the skip guard.

------------------------------------------------------------------------------
Running it for real
------------------------------------------------------------------------------
    make up                 # starts Postgres (pgvector/pg16) on localhost:5432
    createdb chronocanvas_test            # or let the test create it for you
    export SHOWRUNNER_PG_TEST_URL=postgresql+asyncpg://chronocanvas:chronocanvas@localhost:5432/chronocanvas_test
    cd backend && pytest tests/showrunner/test_pg_integration.py -v
        # needs: pip install asyncpg alembic psycopg[binary]

The test creates the target database if it is missing, drops every showrunner
table at teardown (so reruns are idempotent), and never touches the dev `chronocanvas`
database as long as you point SHOWRUNNER_PG_TEST_URL at a separate `_test` db.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

# The app's Settings singleton rejects the insecure default SECRET_KEY for any
# non-sqlite database URL. Set a throwaway key BEFORE chronocanvas.config is
# imported (mirrors backend/tests/conftest.py), so importing the models / engine
# below the skip guard never trips that validation.
os.environ.setdefault("SECRET_KEY", "test-key-not-default-1234567890")

PG_URL = os.environ.get("SHOWRUNNER_PG_TEST_URL")

# Module-level guard: when SHOWRUNNER_PG_TEST_URL is unset the whole module
# skips, and — crucially — nothing below imports asyncpg / alembic / psycopg, so
# collection succeeds in the bare unit-test venv that lacks those packages.
pytestmark = pytest.mark.skipif(
    not PG_URL,
    reason="set SHOWRUNNER_PG_TEST_URL to run the Postgres integration test",
)

# Tables created by migrations 010 + 011 — dropped at teardown for idempotency.
# Order is leaf-first so CASCADE isn't strictly required, but we drop with
# CASCADE anyway to be robust against FK ordering and immutability triggers.
_SHOWRUNNER_TABLES = [
    "budget_reservations",
    "budgets",
    "media_generations",
    "production_artifacts",
    "skill_contributions",
    "specialist_disagreements",
    "approval_gates",
    "audience_choices",
    "beats",
    "branch_proposals",
    "shots",
    "canon_mutations",
    "canon_facts",
    "story_threads",
    "relationships",
    "characters",
    "skill_invocations",
    "episodes",
    "series",
]


def _sync_url(async_url: str) -> str:
    """asyncpg URL -> psycopg (sync) URL, for admin / DDL bootstrap."""
    return async_url.replace("+asyncpg", "+psycopg")


def _ensure_test_database(sync_url: str) -> None:
    """Create the target database if it does not already exist.

    Connects to the cluster's default ``postgres`` maintenance database with
    AUTOCOMMIT (CREATE DATABASE cannot run inside a transaction) and issues
    CREATE DATABASE when the target is missing.
    """
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    url = make_url(sync_url)
    target_db = url.database
    admin_url = url.set(database="postgres")

    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": target_db}
            ).scalar()
            if not exists:
                # Identifier can't be parameterized; target_db comes from our own
                # env var, not user input. Quote it defensively all the same.
                conn.execute(text(f'CREATE DATABASE "{target_db}"'))
    finally:
        admin_engine.dispose()


def _drop_showrunner_tables(sync_url: str) -> None:
    """Drop every showrunner table (CASCADE) so reruns start clean."""
    from sqlalchemy import create_engine, text

    engine = create_engine(sync_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            # alembic_version too, so the next `upgrade head` re-runs migrations.
            for table in [*_SHOWRUNNER_TABLES, "alembic_version"]:
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
    finally:
        engine.dispose()


def _run_alembic_upgrade_head() -> None:
    """Run ``alembic upgrade head`` against the test DB.

    The repo's ``alembic/env.py`` reads ``settings.database_url`` (i.e.
    DATABASE_URL) for the connection, so we point DATABASE_URL at the test DB for
    the duration of the upgrade and drive Alembic in-process. We run it from the
    ``backend`` directory because alembic.ini's ``script_location = alembic`` is
    relative to that directory.
    """
    from alembic.config import Config

    from alembic import command

    backend_dir = Path(__file__).resolve().parents[2]
    alembic_ini = backend_dir / "alembic.ini"
    assert alembic_ini.is_file(), f"alembic.ini not found at {alembic_ini}"

    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    # env.py builds the engine from settings.database_url; override it here so it
    # targets the test database rather than the dev default.
    cfg.set_main_option("sqlalchemy.url", PG_URL)

    prev_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = PG_URL
    try:
        command.upgrade(cfg, "head")
    finally:
        if prev_db_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev_db_url


@pytest.fixture(scope="module")
def migrated_pg():
    """Create the test DB, run migrations to head, yield the async URL, drop tables."""
    # Lazy imports happen inside the helpers above — they only run when this
    # fixture is exercised, i.e. when PG_URL is set and the module did not skip.
    sync_url = _sync_url(PG_URL)

    _ensure_test_database(sync_url)
    # Start from a clean slate even if a previous aborted run left tables behind.
    _drop_showrunner_tables(sync_url)
    _run_alembic_upgrade_head()
    try:
        yield PG_URL
    finally:
        _drop_showrunner_tables(sync_url)


async def test_migrations_create_showrunner_tables(migrated_pg):
    """`alembic upgrade head` reaches head and creates the showrunner tables."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(migrated_pg)
    try:
        async with engine.connect() as conn:
            rows = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
            )
            present = {r[0] for r in rows}
    finally:
        await engine.dispose()

    # A representative spread across migrations 010 + 011.
    for expected in (
        "series",
        "episodes",
        "shots",
        "production_artifacts",
        "media_generations",
        "budgets",
        "budget_reservations",
        "skill_contributions",
    ):
        assert expected in present, f"migration did not create table {expected!r}"


async def test_postgres_specific_crud(migrated_pg):
    """End-to-end CRUD exercising JSONB, ARRAY(UUID), and UUID fidelity."""
    from sqlalchemy import delete, select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    # Import models so every showrunner table is registered on Base.metadata and
    # the ORM mappers are configured.
    from chronocanvas.db.models import (
        Budget,
        BudgetReservation,
        Episode,
        MediaGeneration,
        ProductionArtifact,
        Series,
        Shot,
        SkillContribution,
    )

    engine = create_async_engine(migrated_pg)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        # ---- INSERT: Series + Episode -----------------------------------
        async with sessionmaker() as session:
            series = Series(title="Chola Tide", premise="A dynasty at its zenith.", era="Chola, 10th c.")
            session.add(series)
            await session.flush()
            series_id = series.id

            episode = Episode(series_id=series_id, number=1, title="The Salt March")
            session.add(episode)
            await session.flush()
            episode_id = episode.id

            # ---- INSERT: Shot with JSONB inputs + ARRAY(UUID) depends_on ----
            dep_a = uuid.uuid4()
            dep_b = uuid.uuid4()
            shot = Shot(
                episode_id=episode_id,
                index=0,
                description="Establishing wide of the harbour at dawn.",
                inputs={"prompt": "harbour at dawn", "style_ref": "chola-bronze", "reuse": True},
                depends_on=[dep_a, dep_b],
            )
            session.add(shot)
            await session.flush()
            shot_id = shot.id

            # ---- INSERT: ProductionArtifact with JSONB payload --------------
            artifact = ProductionArtifact(
                episode_id=episode_id,
                shot_id=shot_id,
                kind="image",
                url="gs://bucket/shot0.png",
                cost_usd=0.04,
                payload={"seed": 12345, "model": "imagen-3", "tags": ["dawn", "harbour"]},
            )
            session.add(artifact)

            # ---- INSERT: MediaGeneration ledger row -------------------------
            media = MediaGeneration(
                episode_id=episode_id,
                shot_id=shot_id,
                kind="image",
                provider="gemini",
                model="imagen-3",
                units=1.0,
                unit_cost_usd=0.04,
                cost_usd=0.04,
            )
            session.add(media)

            # ---- INSERT: Budget + BudgetReservation -------------------------
            budget = Budget(scope="episode", scope_id=episode_id, limit_usd=10.0, spent_usd=0.04)
            session.add(budget)
            await session.flush()
            budget_id = budget.id

            reservation = BudgetReservation(
                budget_id=budget_id, amount_usd=0.50, job_id="job-abc", status="active"
            )
            session.add(reservation)

            # ---- INSERT: SkillContribution with JSONB fields ----------------
            contribution = SkillContribution(
                episode_id=episode_id,
                room="writers",
                skill_name="narrative-engineer",
                decision_id="dec-1",
                stance="for",
                summary="Strong hook.",
                fields={"hook_score": 0.9, "notes": ["opens on conflict"]},
            )
            session.add(contribution)

            await session.commit()

        # ---- READ BACK + ASSERT fidelity --------------------------------
        async with sessionmaker() as session:
            got_shot = (
                await session.execute(select(Shot).where(Shot.id == shot_id))
            ).scalar_one()
            # JSONB round-trip
            assert got_shot.inputs == {
                "prompt": "harbour at dawn",
                "style_ref": "chola-bronze",
                "reuse": True,
            }
            # ARRAY(UUID) round-trip — the column SQLite cannot represent.
            assert got_shot.depends_on == [dep_a, dep_b]
            assert all(isinstance(d, uuid.UUID) for d in got_shot.depends_on)

            got_artifact = (
                await session.execute(
                    select(ProductionArtifact).where(ProductionArtifact.shot_id == shot_id)
                )
            ).scalar_one()
            assert got_artifact.payload["seed"] == 12345
            assert got_artifact.payload["tags"] == ["dawn", "harbour"]
            assert isinstance(got_artifact.episode_id, uuid.UUID)

            got_media = (
                await session.execute(
                    select(MediaGeneration).where(MediaGeneration.episode_id == episode_id)
                )
            ).scalar_one()
            assert got_media.provider == "gemini"
            assert got_media.cost_usd == pytest.approx(0.04)

            got_budget = (
                await session.execute(select(Budget).where(Budget.id == budget_id))
            ).scalar_one()
            assert got_budget.scope_id == episode_id  # UUID FK fidelity

            got_reservation = (
                await session.execute(
                    select(BudgetReservation).where(BudgetReservation.budget_id == budget_id)
                )
            ).scalar_one()
            assert got_reservation.amount_usd == pytest.approx(0.50)

            got_contribution = (
                await session.execute(
                    select(SkillContribution).where(SkillContribution.episode_id == episode_id)
                )
            ).scalar_one()
            assert got_contribution.fields == {"hook_score": 0.9, "notes": ["opens on conflict"]}

        # ---- UPDATE (on a mutable table — no immutability guard) ---------
        async with sessionmaker() as session:
            got_shot = (
                await session.execute(select(Shot).where(Shot.id == shot_id))
            ).scalar_one()
            got_shot.status = "ready"
            got_shot.inputs = {**got_shot.inputs, "reuse": False}
            await session.commit()

        async with sessionmaker() as session:
            got_shot = (
                await session.execute(select(Shot).where(Shot.id == shot_id))
            ).scalar_one()
            assert got_shot.status == "ready"
            assert got_shot.inputs["reuse"] is False

        # ---- DELETE (mutable table) -------------------------------------
        async with sessionmaker() as session:
            await session.execute(delete(BudgetReservation).where(BudgetReservation.id == reservation.id))
            await session.commit()

        async with sessionmaker() as session:
            remaining = (
                await session.execute(
                    select(BudgetReservation).where(BudgetReservation.budget_id == budget_id)
                )
            ).scalars().all()
            assert remaining == []
    finally:
        await engine.dispose()
