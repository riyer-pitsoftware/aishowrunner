"""Continuity eval pass tests (TRD §9.4, asr-2in.5).

Runs ``maybe_run_continuity`` against an in-memory SQLite engine with an injected
fake scorer (no network). Covers the gate (eval disabled), a clean pass
(support), a failing pass (concern WARNING — non-blocking, status unchanged), and
a budget cap (BudgetExceeded handled gracefully).

The shot models declare Postgres-only column types (JSONB / ARRAY / UUID); the
shims below teach SQLite to render + bind them so the production code runs
unmodified. Copied verbatim from test_media_regenerate.py — test-only plumbing.
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
from chronocanvas.config import settings
from chronocanvas.db.base import Base
from chronocanvas.db.models.showrunner_cost import Budget
from chronocanvas.db.models.showrunner_episode import Episode, ProductionArtifact, Shot
from chronocanvas.db.models.showrunner_room import SkillContribution
from chronocanvas.showrunner.media.continuity import maybe_run_continuity


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

class _FakePublisher:
    """Captures published payloads (RoomPublisher's injectable backend)."""

    def __init__(self):
        self.events: list[dict] = []

    async def publish(self, channel, payload):  # noqa: ANN001
        self.events.append(payload)

    def types(self):
        return [e["type"] for e in self.events]


def _scorer(score: float, issues=None, summary="ok"):
    """An async scorer seam that returns a fixed verdict (no network)."""
    async def scorer(prompt: str) -> dict:
        return {"score": score, "issues": list(issues or []), "summary": summary}

    return scorer


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


async def _seed_episode(s, *, status="ready", limit_usd=0.0):
    """Seed an episode with two ready shots, each with a v1 artifact. Returns ep."""
    ep = Episode(series_id=uuid.uuid4(), number=1, title="Ep", status=status)
    s.add(ep)
    await s.flush()

    if limit_usd:
        s.add(Budget(scope="episode", scope_id=ep.id, limit_usd=limit_usd,
                     spent_usd=0.0, reserved_usd=0.0))
        await s.flush()

    for i, prompt in enumerate(("a wide shot of the temple", "a close-up of the king")):
        shot = Shot(episode_id=ep.id, index=i, description=prompt,
                    inputs={"kind": "image", "prompt": prompt},
                    depends_on=[], status="ready")
        s.add(shot)
        await s.flush()
        art = ProductionArtifact(episode_id=ep.id, shot_id=shot.id, kind="image",
                                 url=f"/output/shot-{i}-v1.png", mime_type="image/png",
                                 version=1, cost_usd=0.0)
        s.add(art)
        await s.flush()
        shot.artifact_id = art.id
    await s.flush()
    return ep


async def _contributions(s, episode_id):
    rows = await s.execute(
        SkillContribution.__table__.select().where(
            SkillContribution.episode_id == episode_id
        )
    )
    return rows.mappings().all()


# ── Tests ────────────────────────────────────────────────────────────────────

async def test_disabled_returns_none_and_writes_nothing(session, monkeypatch):
    monkeypatch.setattr(settings, "eval_enabled", False)
    ep = await _seed_episode(session)
    pub = _FakePublisher()

    result = await maybe_run_continuity(
        session, ep.id, publisher=pub, scorer=_scorer(0.9)
    )

    assert result is None
    assert await _contributions(session, ep.id) == []
    assert pub.events == []


async def test_clean_pass_writes_support_contribution(session, monkeypatch):
    monkeypatch.setattr(settings, "eval_enabled", True)
    ep = await _seed_episode(session)
    pub = _FakePublisher()

    result = await maybe_run_continuity(
        session, ep.id, publisher=pub,
        scorer=_scorer(0.9, issues=[], summary="No contradictions found."),
    )

    assert result is not None
    assert result["passed"] is True
    assert result["score"] == 0.9

    rows = await _contributions(session, ep.id)
    assert len(rows) == 1
    row = rows[0]
    assert row["room"] == "production_desk"
    assert row["skill_name"] == "continuity-eval"
    assert row["stance"] == "support"
    assert row["fields"]["score"] == 0.9
    assert row["fields"]["passed"] is True
    assert result["contribution_id"] == str(row["id"])

    # A production_stage event was emitted for the live Production Desk.
    assert "production_stage" in pub.types()
    stage = next(e for e in pub.events if e["type"] == "production_stage")
    assert stage["stage"] == "continuity" and stage["passed"] is True


async def test_low_score_is_concern_warning_not_block(session, monkeypatch):
    monkeypatch.setattr(settings, "eval_enabled", True)
    ep = await _seed_episode(session, status="ready")
    pub = _FakePublisher()

    result = await maybe_run_continuity(
        session, ep.id, publisher=pub,
        scorer=_scorer(0.3, issues=["king's robe changes color between shots"],
                       summary="Wardrobe continuity breaks."),
    )

    # Non-blocking: returns a verdict, never raises.
    assert result is not None
    assert result["passed"] is False
    assert result["score"] == 0.3

    rows = await _contributions(session, ep.id)
    assert len(rows) == 1
    row = rows[0]
    # Low score → "concern" (a warning), NOT "block".
    assert row["stance"] == "concern"
    assert row["stance"] != "block"
    assert "king's robe changes color between shots" in row["risks"]

    # Episode lifecycle is untouched by the eval.
    await session.refresh(ep)
    assert ep.status == "ready"


async def test_budget_exceeded_handled_gracefully(session, monkeypatch):
    monkeypatch.setattr(settings, "eval_enabled", True)
    # Force a positive eval estimate so a tiny cap blocks the reservation.
    import chronocanvas.showrunner.media.continuity as cont

    monkeypatch.setattr(cont, "estimate_production", lambda *a, **k: 1.0)
    ep = await _seed_episode(session, limit_usd=0.001)
    pub = _FakePublisher()

    result = await maybe_run_continuity(
        session, ep.id, publisher=pub, scorer=_scorer(0.9)
    )

    # Returns gracefully without scoring; nothing persisted; a warning emitted.
    assert result is None
    assert await _contributions(session, ep.id) == []
    assert "budget_warning" in pub.types()
