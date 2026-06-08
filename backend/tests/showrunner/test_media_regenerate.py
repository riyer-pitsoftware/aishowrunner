"""Selective regeneration tests (TRD §9.3, asr-2in.3 + budget enforcement asr-3mk.6).

Runs the full DB-backed DAG walk against an in-memory SQLite engine. The shot
models declare Postgres-only column types (JSONB / ARRAY / UUID); the shims below
teach SQLite to render + bind them so the production code runs unmodified. This is
test-only plumbing — nothing in ``src`` is touched.

Scenario: a → b → c (c depends on b, b depends on a). ``c`` is APPROVED (locked).
Regenerating ``a`` must regenerate a and b (new artifact at version 2 with a
compare payload, prior artifact preserved) while leaving ``c`` untouched.
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
from chronocanvas.db.models.showrunner_episode import (
    Episode,
    ProductionArtifact,
    Shot,
)
from chronocanvas.showrunner.media.base import MediaArtifact
from chronocanvas.showrunner.media.regenerate import Providers, regenerate_shot


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
Shot.__table__.c.depends_on.type = _UUIDArray()


# ── Fakes ────────────────────────────────────────────────────────────────────

class _FakeImageProvider:
    name = "fake"

    def __init__(self):
        self.calls = 0

    async def generate_image(self, prompt, *, output_dir, width=1080, height=1920, **kw):
        self.calls += 1
        return MediaArtifact(
            kind="image",
            url=f"/output/regen-{self.calls}.png",
            mime_type="image/png",
            units=1.0,
            provider="fake",
            model="fake-image",
        )


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
    """Captures published payloads (RoomPublisher's injectable backend)."""

    def __init__(self):
        self.events: list[dict] = []

    async def publish(self, channel, payload):  # noqa: ANN001
        self.events.append(payload)

    def types(self):
        return [e["type"] for e in self.events]


def _fake_providers():
    return Providers(image=_FakeImageProvider(), video=_FakeVideoProvider(), tts=_FakeTTSProvider())


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


async def _seed_chain(s, *, c_status="approved", limit_usd=0.0):
    """Seed an episode + a→b→c chain, each with a v1 artifact. Returns ids."""
    ep = Episode(series_id=uuid.uuid4(), number=1, title="Ep")
    s.add(ep)
    await s.flush()

    if limit_usd:
        s.add(Budget(scope="episode", scope_id=ep.id, limit_usd=limit_usd,
                     spent_usd=0.0, reserved_usd=0.0))

    a = Shot(episode_id=ep.id, index=0, inputs={"kind": "image", "prompt": "a"},
             depends_on=[], status="ready")
    s.add(a)
    await s.flush()
    b = Shot(episode_id=ep.id, index=1, inputs={"kind": "image", "prompt": "b"},
             depends_on=[a.id], status="ready")
    s.add(b)
    await s.flush()
    c = Shot(episode_id=ep.id, index=2, inputs={"kind": "image", "prompt": "c"},
             depends_on=[b.id], status=c_status)
    s.add(c)
    await s.flush()

    for shot in (a, b, c):
        art = ProductionArtifact(episode_id=ep.id, shot_id=shot.id, kind="image",
                                 url=f"/output/{shot.inputs['prompt']}-v1.png",
                                 mime_type="image/png", version=1, cost_usd=0.0)
        s.add(art)
        await s.flush()
        shot.artifact_id = art.id
    await s.flush()
    return ep, a, b, c


# ── Tests ────────────────────────────────────────────────────────────────────

async def test_regenerate_walks_stale_and_preserves_approved(session):
    ep, a, b, c = await _seed_chain(session)
    c_artifact_before = c.artifact_id
    pub = _FakePublisher()

    summary = await regenerate_shot(
        session, ep.id, a.id, publisher=pub, providers=_fake_providers()
    )

    # a and b regenerated, in dependency order; c preserved (approved, locked).
    assert summary["regenerated"] == [str(a.id), str(b.id)]
    assert summary["preserved"] == [str(c.id)]
    assert summary["skipped"] == []

    await session.refresh(a)
    await session.refresh(b)
    await session.refresh(c)
    assert a.status == "ready" and b.status == "ready"
    assert c.status == "approved" and c.artifact_id == c_artifact_before

    # Each regenerated shot has a NEW v2 artifact with a compare block...
    for shot, prompt in ((a, "a"), (b, "b")):
        arts = (await session.execute(
            ProductionArtifact.__table__.select().where(
                ProductionArtifact.shot_id == shot.id
            )
        )).mappings().all()
        versions = sorted(r["version"] for r in arts)
        assert versions == [1, 2]  # prior artifact preserved alongside the new one
        v2 = next(r for r in arts if r["version"] == 2)
        compare = v2["payload"]["compare"]
        assert compare["prev_url"] == f"/output/{prompt}-v1.png"
        assert compare["new_url"] == v2["url"]
        assert compare["prev_artifact_id"] is not None
        assert shot.artifact_id == v2["id"]

    # c keeps exactly its single v1 artifact (untouched).
    c_arts = (await session.execute(
        ProductionArtifact.__table__.select().where(ProductionArtifact.shot_id == c.id)
    )).mappings().all()
    assert [r["version"] for r in c_arts] == [1]

    # Ledger rows written for the two regenerated shots only.
    gens = (await session.execute(MediaGeneration.__table__.select())).mappings().all()
    assert {r["shot_id"] for r in gens} == {a.id, b.id}

    # Events: a regenerate stage + two artifact_ready.
    assert "production_stage" in pub.types()
    assert pub.types().count("artifact_ready") == 2


async def test_budget_exceeded_handled_without_crash(session):
    # Tiny cap with nonzero image pricing so the first reserve blocks.
    import chronocanvas.showrunner.media.regenerate as regen

    # Force a positive image price regardless of config/pricing.yaml contents.
    monkey_pricing = {"media": {"image": {"unit": "per_image", "price": 1.0}}}
    orig_load = regen.load_pricing
    regen.load_pricing = lambda *a, **k: monkey_pricing
    try:
        ep, a, b, c = await _seed_chain(session, c_status="ready", limit_usd=0.001)
        pub = _FakePublisher()
        summary = await regenerate_shot(
            session, ep.id, a.id, publisher=pub, providers=_fake_providers()
        )
    finally:
        regen.load_pricing = orig_load

    # No crash; nothing regenerated; budget_exceeded emitted.
    assert summary["regenerated"] == []
    assert "budget_exceeded" in pub.types()
    # The whole stale set was skipped (not silently marked ready).
    assert set(summary["skipped"]) == {str(a.id), str(b.id), str(c.id)}
