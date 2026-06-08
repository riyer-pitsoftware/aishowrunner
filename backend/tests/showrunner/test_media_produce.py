"""Plan → media generation tests (TRD §9.2, asr-2in.2 + budget enforcement asr-3mk.6).

DB-backed DAG walk against in-memory SQLite. Shot models declare Postgres-only
column types (JSONB / ARRAY / UUID); the shims below teach SQLite to render them
so production code runs unmodified. Test-only plumbing — nothing in ``src`` is
touched.

Covers: dependency-ordered generation with artifact + ledger rows and episode
advance; APPROVED shots preserved; a hard budget breach stopping the run
gracefully; and an isolated per-shot generation failure.
"""

from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy import types
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

import chronocanvas.db.models  # noqa: F401  (register all tables on Base.metadata)
from chronocanvas.db.base import Base
from chronocanvas.db.models.showrunner_cost import Budget, MediaGeneration
from chronocanvas.db.models.showrunner_episode import Episode, ProductionArtifact, Shot
from chronocanvas.showrunner.episodes.state import EpisodeStatus
from chronocanvas.showrunner.media.base import MediaArtifact
from chronocanvas.showrunner.media.produce import Providers, produce_episode


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


Shot.__table__.c.depends_on.type = _UUIDArray()


# ── Fakes ────────────────────────────────────────────────────────────────────

class _FakeImageProvider:
    name = "fake"

    def __init__(self, order: list[str]):
        self.order = order  # shared call-order log (prompt text)
        self.calls = 0

    async def generate_image(self, prompt, *, output_dir, width=1080, height=1920, **kw):
        self.calls += 1
        self.order.append(prompt)
        return MediaArtifact(
            kind="image", url=f"/output/img-{self.calls}.png", mime_type="image/png",
            units=1.0, provider="fake", model="fake-image",
        )


class _FailingImageProvider:
    name = "boom"

    async def generate_image(self, prompt, *, output_dir, width=1080, height=1920, **kw):
        raise RuntimeError("provider exploded")


class _FakeVideoProvider:
    name = "fake"

    async def generate_video(self, prompt, *, output_dir, seconds=8.0, image_url=None, **kw):
        return MediaArtifact(kind="video", url="/output/v.mp4", mime_type="video/mp4",
                             units=float(seconds), provider="fake", model="fake-video")


class _FakeTTSProvider:
    name = "fake"

    async def synthesize(self, text, *, output_dir, voice=None, **kw):
        return MediaArtifact(kind="tts", url="/output/a.wav", mime_type="audio/wav",
                             units=float(len(text)), provider="fake", model="fake-tts")


class _FakePublisher:
    def __init__(self):
        self.events: list[dict] = []

    async def publish(self, channel, payload):  # noqa: ANN001
        self.events.append(payload)

    def types(self):
        return [e["type"] for e in self.events]


def _providers(order=None):
    return Providers(
        image=_FakeImageProvider(order if order is not None else []),
        video=_FakeVideoProvider(),
        tts=_FakeTTSProvider(),
    )


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


async def _seed(s, *, c_status="pending", limit_usd=0.0):
    """Episode (greenlit, ready to produce) + a→b chain + optional approved c."""
    ep = Episode(series_id=uuid.uuid4(), number=1, title="Ep",
                 status=EpisodeStatus.EPISODE_GREENLIGHT.value)
    s.add(ep)
    await s.flush()
    if limit_usd:
        s.add(Budget(scope="episode", scope_id=ep.id, limit_usd=limit_usd,
                     spent_usd=0.0, reserved_usd=0.0))

    a = Shot(episode_id=ep.id, index=0, inputs={"kind": "image", "prompt": "a"},
             depends_on=[], status="pending")
    s.add(a)
    await s.flush()
    b = Shot(episode_id=ep.id, index=1, inputs={"kind": "image", "prompt": "b"},
             depends_on=[a.id], status="pending")
    s.add(b)
    await s.flush()
    c = Shot(episode_id=ep.id, index=2, inputs={"kind": "image", "prompt": "c"},
             depends_on=[], status=c_status)
    s.add(c)
    await s.flush()
    return ep, a, b, c


# ── Tests ────────────────────────────────────────────────────────────────────

async def test_produce_walks_dag_and_writes_artifacts(session):
    ep, a, b, c = await _seed(session, c_status="approved")
    order: list[str] = []
    pub = _FakePublisher()

    summary = await produce_episode(
        session, ep.id, publisher=pub, providers=_providers(order)
    )

    # a, b produced (dependency order); c approved → preserved/skipped.
    assert summary["produced"] == 2
    assert summary["skipped"] == 1
    assert summary["failed"] == 0
    assert summary["stopped"] is False
    assert order == ["a", "b"]  # upstream before downstream

    for shot in (a, b):
        await session.refresh(shot)
        assert shot.status == "ready"
        assert shot.artifact_id is not None
    await session.refresh(c)
    assert c.status == "approved"

    arts = (await session.execute(ProductionArtifact.__table__.select())).mappings().all()
    assert {r["shot_id"] for r in arts} == {a.id, b.id}
    assert all(r["version"] == 1 for r in arts)

    gens = (await session.execute(MediaGeneration.__table__.select())).mappings().all()
    assert {r["shot_id"] for r in gens} == {a.id, b.id}
    assert all(r["status"] == "ok" for r in gens)

    assert pub.types().count("artifact_ready") == 2

    # Episode advanced greenlight → producing → final_cut after a clean pass.
    await session.refresh(ep)
    assert ep.status == EpisodeStatus.FINAL_CUT.value


async def test_budget_breach_stops_gracefully(session):
    import chronocanvas.showrunner.media.produce as prod

    monkey_pricing = {"media": {"image": {"unit": "per_image", "price": 1.0}}}
    orig = prod.load_pricing
    prod.load_pricing = lambda *a, **k: monkey_pricing
    try:
        ep, a, b, c = await _seed(session, limit_usd=0.001)
        pub = _FakePublisher()
        summary = await produce_episode(
            session, ep.id, publisher=pub, providers=_providers()
        )
    finally:
        prod.load_pricing = orig

    assert summary["produced"] == 0
    assert summary["stopped"] is True
    assert "budget_exceeded" in pub.types()
    # Episode never reaches FINAL_CUT on a stopped run.
    await session.refresh(ep)
    assert ep.status != EpisodeStatus.FINAL_CUT.value


async def test_generation_failure_is_isolated(session):
    ep, a, b, c = await _seed(session, c_status="approved")
    pub = _FakePublisher()
    bad = Providers(image=_FailingImageProvider(), video=_FakeVideoProvider(),
                    tts=_FakeTTSProvider())

    summary = await produce_episode(session, ep.id, publisher=pub, providers=bad)

    # Both image shots fail but the run completes without raising.
    assert summary["failed"] == 2
    assert summary["produced"] == 0
    for shot in (a, b):
        await session.refresh(shot)
        assert shot.status == "failed"
    # A failed ledger row is recorded per failed shot.
    gens = (await session.execute(MediaGeneration.__table__.select())).mappings().all()
    assert all(r["status"] == "failed" for r in gens)
    assert len(gens) == 2
