"""Shot planner tests (asr-uac, TRD §9.1).

The planner *creates* the ``Shot`` DAG that ``produce``/``regenerate`` later
walk. These tests run it against an in-memory SQLite engine, with the same
Postgres-type shims used by the regenerate tests so the production code runs
unmodified (test-only plumbing — nothing in ``src`` is touched).

Covers: beat-derived plan (ordered, acyclic, valid kinds); default fallback
when the episode has no plan data; idempotency (replace=False is a no-op,
replace=True re-plans but preserves approved shots); and that the produced
shots are shaped so ``produce.produce_episode`` could consume them.
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
from chronocanvas.db.models.showrunner_episode import Beat, Episode, Shot
from chronocanvas.db.models.showrunner_room import SkillContribution
from chronocanvas.showrunner.media.dag import topo_order
from chronocanvas.showrunner.media.planner import plan_shots


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


class _FakePublisher:
    """Captures published payloads (RoomPublisher's injectable backend)."""

    def __init__(self):
        self.events: list[dict] = []

    async def publish(self, channel, payload):  # noqa: ANN001
        self.events.append(payload)

    def types(self):
        return [e["type"] for e in self.events]


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


async def _episode(s, **kw):
    ep = Episode(series_id=uuid.uuid4(), number=1, title=kw.pop("title", "Ep"), **kw)
    s.add(ep)
    await s.flush()
    return ep


def _assert_valid_dag(shots: list[Shot]):
    """Every depends_on points at an earlier shot; the whole graph topo-sorts."""
    by_id = {s.id: s for s in shots}
    index_of = {s.id: s.index for s in shots}
    for s in shots:
        for dep in s.depends_on or []:
            assert dep in by_id, "depends_on references a non-existent shot"
            assert index_of[dep] < s.index, "depends_on must reference an earlier shot"
    topo_order({s.id: list(s.depends_on or []) for s in shots})


def _valid_kinds(shots: list[Shot]):
    for s in shots:
        kind = (s.inputs or {})["kind"]
        assert kind in {"image", "video", "tts"}
        if kind == "tts":
            assert "text" in s.inputs
        else:
            assert "prompt" in s.inputs


async def _shots(s, episode_id) -> list[Shot]:
    from sqlalchemy import select

    rows = await s.execute(select(Shot).where(Shot.episode_id == episode_id).order_by(Shot.index))
    return list(rows.scalars().all())


# ── Tests ────────────────────────────────────────────────────────────────────

async def test_plan_from_beats_is_ordered_and_acyclic(session):
    ep = await _episode(session)
    for i, desc in enumerate(["A river at dawn", "The messenger arrives", "The city burns"]):
        session.add(Beat(episode_id=ep.id, index=i, description=desc))
    await session.flush()

    pub = _FakePublisher()
    result = await plan_shots(session, ep.id, publisher=pub)

    shots = await _shots(session, ep.id)
    # 3 visual beats + 1 closing narration.
    assert result["count"] == 4
    assert len(shots) == 4
    # Indices are 0..n contiguous.
    assert [s.index for s in shots] == [0, 1, 2, 3]

    _assert_valid_dag(shots)
    _valid_kinds(shots)

    images = [s for s in shots if s.inputs["kind"] == "image"]
    narration = [s for s in shots if s.inputs["kind"] == "tts"]
    assert len(images) == 3
    assert len(narration) == 1
    # The beat descriptions made it into the image prompts, in order.
    assert images[0].inputs["prompt"] == "A river at dawn"
    assert images[2].inputs["prompt"] == "The city burns"
    # Narration depends on every visual shot.
    assert set(narration[0].depends_on) == {im.id for im in images}

    assert "production_stage" in pub.types()
    plan_event = next(e for e in pub.events if e.get("stage") == "plan")
    assert plan_event["count"] == 4


async def test_skill_breakdown_is_preferred(session):
    ep = await _episode(session)
    # A beat exists, but a production-desk contribution carries a richer breakdown.
    session.add(Beat(episode_id=ep.id, index=0, description="ignored beat"))
    session.add(
        SkillContribution(
            episode_id=ep.id,
            room="production_desk",
            skill_name="line-producer",
            fields={"shots": [{"prompt": "Wide establishing"}, {"prompt": "Close on face"}]},
        )
    )
    await session.flush()

    result = await plan_shots(session, ep.id, publisher=_FakePublisher())
    shots = await _shots(session, ep.id)
    images = [s for s in shots if s.inputs["kind"] == "image"]
    assert [im.inputs["prompt"] for im in images] == ["Wide establishing", "Close on face"]
    assert result["count"] == 3  # 2 images + narration
    _assert_valid_dag(shots)


async def test_default_fallback_yields_nonempty_plan(session):
    ep = await _episode(session, premise="A spice merchant outwits a corrupt official.")

    result = await plan_shots(session, ep.id, publisher=_FakePublisher())
    shots = await _shots(session, ep.id)
    assert result["count"] >= 2  # at least one visual + narration
    assert any(s.inputs["kind"] == "image" for s in shots)
    assert any(s.inputs["kind"] == "tts" for s in shots)
    _assert_valid_dag(shots)
    _valid_kinds(shots)


async def test_idempotent_no_replace_does_not_duplicate(session):
    ep = await _episode(session)
    for i in range(3):
        session.add(Beat(episode_id=ep.id, index=i, description=f"beat {i}"))
    await session.flush()

    first = await plan_shots(session, ep.id, publisher=_FakePublisher())
    first_ids = {sh["id"] for sh in first["shots"]}

    second = await plan_shots(session, ep.id, publisher=_FakePublisher())
    assert second["count"] == first["count"]
    assert {sh["id"] for sh in second["shots"]} == first_ids

    shots = await _shots(session, ep.id)
    assert len(shots) == first["count"]


async def test_replace_replans_but_preserves_approved(session):
    ep = await _episode(session)
    for i in range(3):
        session.add(Beat(episode_id=ep.id, index=i, description=f"beat {i}"))
    await session.flush()

    await plan_shots(session, ep.id, publisher=_FakePublisher())
    shots = await _shots(session, ep.id)
    # Approve the first shot — it must survive a replace re-plan.
    approved = shots[0]
    approved.status = "approved"
    approved_id = approved.id
    await session.flush()

    result = await plan_shots(session, ep.id, replace=True, publisher=_FakePublisher())
    after = await _shots(session, ep.id)

    # The approved shot is still present...
    ids_after = {s.id for s in after}
    assert approved_id in ids_after
    surviving = next(s for s in after if s.id == approved_id)
    assert surviving.status == "approved"
    # ...the rest were re-planned (new ids), and the graph is still a valid DAG.
    new_ids = ids_after - {approved_id}
    assert new_ids  # fresh shots were created
    assert result["count"] == len(after)
    _assert_valid_dag(after)
    assert [s.index for s in after] == list(range(len(after)))


async def test_planned_shots_are_produce_ready(session):
    """Sanity: the shapes match what ``produce.produce_episode`` consumes."""
    from chronocanvas.showrunner.media.produce import _expected_units

    ep = await _episode(session)
    for i in range(2):
        session.add(Beat(episode_id=ep.id, index=i, description=f"scene {i}"))
    await session.flush()

    await plan_shots(session, ep.id, publisher=_FakePublisher())
    shots = await _shots(session, ep.id)

    # produce reads inputs["kind"] and the per-kind fields; depends_on topo-sorts.
    deps = {s.id: list(s.depends_on or []) for s in shots}
    order = topo_order(deps)
    assert len(order) == len(shots)
    for s in shots:
        kind = s.inputs["kind"]
        assert kind in {"image", "video", "tts"}
        # _expected_units must not raise on the planned inputs.
        assert _expected_units(kind, s.inputs) >= 0.0
        assert s.status == "pending"
