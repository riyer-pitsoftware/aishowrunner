"""Seeded historical-noir demo series tests (asr-av5.4, PRD §9.3.7).

Runs ``seed_showrunner_demo`` against an in-memory SQLite engine. The showrunner
models declare Postgres-only column types (JSONB / ARRAY / UUID); the shims below
teach SQLite to render + bind them so the production code runs unmodified — this
is test-only plumbing copied from ``test_media_regenerate.py``; nothing in
``src`` is touched.

Asserts the series + its canon facts / characters / relationships / threads +
the demo episode and its beats are created, and that re-running the loader is
idempotent (no duplicate series).
"""

from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy import select, types
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

import chronocanvas.db.models  # noqa: F401  (register all tables on Base.metadata)
from chronocanvas.db.base import Base
from chronocanvas.db.models.showrunner_episode import Beat, Episode
from chronocanvas.db.models.showrunner_series import (
    CanonFact,
    Character,
    Relationship,
    Series,
    StoryThread,
)
from chronocanvas.seed.showrunner_demo import DEMO, seed_showrunner_demo


# ── SQLite compatibility shims for the Postgres column types ─────────────────

@compiles(JSONB, "sqlite")
def _compile_jsonb(element, compiler, **kw):  # noqa: ANN001
    return "JSON"


@compiles(PGUUID, "sqlite")
def _compile_uuid(element, compiler, **kw):  # noqa: ANN001
    return "CHAR(32)"


@compiles(ARRAY, "sqlite")
def _compile_array(element, compiler, **kw):  # noqa: ANN001
    return "JSON"


class _UUIDArray(types.TypeDecorator):
    """JSON-encode a list[UUID] so SQLite can store ``Shot.depends_on``."""

    impl = types.Text
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: ANN001
        if value is None:
            return None
        return json.dumps([str(v) for v in value])

    def process_result_value(self, value, dialect):  # noqa: ANN001
        if value is None:
            return None
        return [uuid.UUID(v) for v in json.loads(value)]


# Swap the array column type for the SQLite test engine (in-memory metadata only).
from chronocanvas.db.models.showrunner_episode import Shot  # noqa: E402

Shot.__table__.c.depends_on.type = _UUIDArray()


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


# ── Tests ────────────────────────────────────────────────────────────────────

async def test_seed_creates_series_canon_and_episode(session):
    series = await seed_showrunner_demo(session)
    await session.flush()

    # Series created, active, with the historical-noir content.
    assert series.title == DEMO["series"]["title"]
    assert series.status == "active"
    assert series.era == DEMO["series"]["era"]
    assert series.creative_rules.get("tone") == "historical noir"

    # Canon facts materialized (snapshot table) for every seeded fact.
    facts = (
        await session.execute(select(CanonFact).where(CanonFact.series_id == series.id))
    ).scalars().all()
    assert len(facts) == len(DEMO["facts"])
    assert {f.fact_key for f in facts} == {f["key"] for f in DEMO["facts"]}
    assert all(f.status == "active" for f in facts)

    # Characters + relationships + open threads.
    chars = (
        await session.execute(select(Character).where(Character.series_id == series.id))
    ).scalars().all()
    assert {c.slug for c in chars} == {c["slug"] for c in DEMO["characters"]}

    rels = (
        await session.execute(
            select(Relationship).where(Relationship.series_id == series.id)
        )
    ).scalars().all()
    assert len(rels) == len(DEMO["relationships"])

    threads = (
        await session.execute(
            select(StoryThread).where(StoryThread.series_id == series.id)
        )
    ).scalars().all()
    assert len(threads) == len(DEMO["threads"])
    assert all(t.status == "open" for t in threads)

    # Demo episode parked in the Story Room with a beat sheet + Beat rows.
    episode = (
        await session.execute(select(Episode).where(Episode.series_id == series.id))
    ).scalar_one()
    assert episode.status == "story_room"
    assert episode.title == DEMO["episode"]["title"]
    assert len(episode.beat_sheet["beats"]) == len(DEMO["episode"]["beats"])

    beats = (
        await session.execute(
            select(Beat).where(Beat.episode_id == episode.id).order_by(Beat.index)
        )
    ).scalars().all()
    assert len(beats) == len(DEMO["episode"]["beats"])
    # Beats carry a visual prompt the shot planner can expand.
    assert all(b.payload.get("visual") for b in beats)


async def test_seed_folds_into_canon_rail(session):
    """Mutations were appended, so the folded canon rail is populated."""
    series = await seed_showrunner_demo(session)
    await session.flush()

    from chronocanvas.showrunner.series.service import CanonService

    canon = await CanonService(session).get_canon(series.id)
    assert len(canon["facts"]) == len(DEMO["facts"])
    assert len(canon["characters"]) == len(DEMO["characters"])
    assert len(canon["threads"]["open"]) == len(DEMO["threads"])


async def test_seed_is_idempotent(session):
    first = await seed_showrunner_demo(session)
    await session.flush()
    second = await seed_showrunner_demo(session)
    await session.flush()

    # Same series returned, not a duplicate.
    assert first.id == second.id
    all_series = (
        await session.execute(
            select(Series).where(Series.title == DEMO["series"]["title"])
        )
    ).scalars().all()
    assert len(all_series) == 1

    # Canon rows not duplicated on the second run.
    facts = (
        await session.execute(select(CanonFact).where(CanonFact.series_id == first.id))
    ).scalars().all()
    assert len(facts) == len(DEMO["facts"])
    episodes = (
        await session.execute(select(Episode).where(Episode.series_id == first.id))
    ).scalars().all()
    assert len(episodes) == 1
