"""Plan → Shot DAG (TRD §9.1) — turn an episode's approved plan into shot rows.

``produce``/``regenerate`` walk a ``Shot`` DAG, but nothing else creates those
rows: this planner is the missing first stage. It derives a deterministic,
acyclic shot list from whatever plan data the episode carries (in priority
order: a production-desk skill's structured shot breakdown → ``Beat`` rows →
``Episode.beat_sheet`` → a default fallback from the premise/branch), then
persists ``Shot`` rows shaped exactly the way ``produce`` consumes them
(``inputs["kind"]`` ∈ {image, tts, ...}, ``depends_on`` a real DAG).

The output is intentionally simple and coherent: one image shot per visual
beat (each chained to the previous so generation is ordered), followed by a
single closing narration (``tts``) shot that depends on every visual shot.

Idempotent: re-planning without ``replace`` returns the existing shots; with
``replace`` it drops the non-approved shots (preserving ``approved`` ones) and
re-plans. The persisted graph is validated to be acyclic before returning.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.showrunner.episodes.service import EpisodeService
from chronocanvas.showrunner.media.dag import topo_order
from chronocanvas.showrunner.rooms.events import EventType, RoomPublisher

logger = logging.getLogger(__name__)

# Production-desk rooms whose skill contributions may carry a shot breakdown.
PRODUCTION_ROOMS = ("production_desk", "production", "media")
DEFAULT_SHOT_COUNT = 3


class _PlannedShot:
    """A single shot before it is persisted (a visual image or a narration)."""

    __slots__ = ("kind", "description", "prompt", "text", "voice")

    def __init__(self, kind: str, *, description=None, prompt=None, text=None, voice=None):
        self.kind = kind
        self.description = description
        self.prompt = prompt
        self.text = text
        self.voice = voice

    def inputs(self) -> dict:
        if self.kind == "tts":
            return {"kind": "tts", "text": self.text or "", "voice": self.voice}
        return {"kind": "image", "prompt": self.prompt or self.description or ""}


def _str(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _shots_from_breakdown(items: list) -> list[str]:
    """Extract per-shot visual prompts from a structured breakdown list.

    Each item may be a string, or a dict with one of several plausible keys for
    the visual prompt (``prompt``/``visual``/``description``/``shot``/``scene``).
    Returns the ordered list of non-empty prompts.
    """
    prompts: list[str] = []
    for item in items:
        if isinstance(item, str):
            text = _str(item)
        elif isinstance(item, dict):
            text = ""
            for key in ("prompt", "visual", "visual_prompt", "description", "shot", "scene", "text"):
                text = _str(item.get(key))
                if text:
                    break
        else:
            text = ""
        if text:
            prompts.append(text)
    return prompts


async def _breakdown_prompts(session: AsyncSession, episode_id: uuid.UUID) -> list[str]:
    """Look for a production-desk skill contribution carrying a shot breakdown.

    Searches ``fields`` then ``recommendations`` for the first list of shots /
    scenes (under a handful of plausible keys). Returns the ordered prompts, or
    an empty list if no contribution provides one.
    """
    from chronocanvas.db.models.showrunner_room import SkillContribution

    rows = await session.execute(
        select(SkillContribution)
        .where(SkillContribution.episode_id == episode_id)
        .where(SkillContribution.room.in_(PRODUCTION_ROOMS))
        .order_by(SkillContribution.created_at)
    )
    for contribution in rows.scalars().all():
        for source in (contribution.fields, contribution.recommendations):
            if isinstance(source, dict):
                for key in ("shots", "shot_breakdown", "scenes", "storyboard", "breakdown"):
                    value = source.get(key)
                    if isinstance(value, list) and value:
                        prompts = _shots_from_breakdown(value)
                        if prompts:
                            return prompts
            elif isinstance(source, list) and source:
                prompts = _shots_from_breakdown(source)
                if prompts:
                    return prompts
    return []


async def _beat_prompts(session: AsyncSession, episode_id: uuid.UUID) -> list[str]:
    """One visual prompt per ``Beat`` row, in beat order."""
    from chronocanvas.db.models.showrunner_episode import Beat

    rows = await session.execute(
        select(Beat).where(Beat.episode_id == episode_id).order_by(Beat.index)
    )
    prompts: list[str] = []
    for beat in rows.scalars().all():
        payload = beat.payload if isinstance(beat.payload, dict) else {}
        prompt = _str(payload.get("visual")) or _str(payload.get("prompt")) or _str(beat.description)
        if prompt:
            prompts.append(prompt)
    return prompts


def _beat_sheet_prompts(beat_sheet) -> list[str]:
    """Visual prompts from ``Episode.beat_sheet`` (``beats`` or ``scenes`` list)."""
    if not isinstance(beat_sheet, dict):
        return []
    for key in ("beats", "scenes", "shots"):
        value = beat_sheet.get(key)
        if isinstance(value, list) and value:
            prompts = _shots_from_breakdown(value)
            if prompts:
                return prompts
    return []


async def _default_prompts(session: AsyncSession, episode) -> list[str]:
    """Fallback 3-shot plan derived from the premise / selected branch."""
    from chronocanvas.db.models.showrunner_episode import BranchProposal

    premise = _str(episode.premise) or _str(episode.title)
    branch_line = ""
    rows = await session.execute(
        select(BranchProposal)
        .where(BranchProposal.episode_id == episode.id)
        .where(BranchProposal.selected.is_(True))
    )
    branch = rows.scalars().first()
    if branch is not None:
        branch_line = _str(branch.hook) or _str(branch.summary) or _str(branch.title)

    subject = premise or branch_line or "the episode"
    beats = [
        f"Establishing shot: {subject}",
        f"Rising action: {branch_line or subject}",
        f"Climactic closing shot: {subject}",
    ]
    return beats[:DEFAULT_SHOT_COUNT]


def _narration_text(prompts: list[str], episode) -> str:
    """A single closing-narration line summarising the planned visuals."""
    premise = _str(episode.premise) or _str(episode.title)
    if premise:
        return premise
    return " ".join(prompts) if prompts else "Narration."


async def plan_shots(
    session: AsyncSession,
    episode_id: uuid.UUID,
    *,
    publisher=None,
    replace: bool = False,
) -> dict:
    """Derive and persist an ordered, acyclic ``Shot`` DAG for ``episode_id``.

    Returns ``{"shots": [{id, index, kind, depends_on}, ...], "count": N}``.
    """
    from chronocanvas.config import settings
    from chronocanvas.db.models.showrunner_episode import Shot

    pub = RoomPublisher(str(episode_id), publisher)
    episodes = EpisodeService(session)

    episode = await episodes.get(episode_id)
    if episode is None:
        logger.warning("plan_shots: episode %s not found", episode_id)
        return {"shots": [], "count": 0}

    existing_rows = await session.execute(
        select(Shot).where(Shot.episode_id == episode_id).order_by(Shot.index)
    )
    existing = list(existing_rows.scalars().all())

    if existing and not replace:
        # Idempotent: return the existing plan without duplicating.
        return _summary(existing)

    preserved: list[Shot] = []
    if existing and replace:
        for shot in existing:
            if shot.status == "approved":
                preserved.append(shot)
            else:
                await session.delete(shot)
        await session.flush()

    # Resolve the visual prompts from the highest-priority source available.
    prompts = await _breakdown_prompts(session, episode_id)
    if not prompts:
        prompts = await _beat_prompts(session, episode_id)
    if not prompts:
        prompts = _beat_sheet_prompts(episode.beat_sheet)
    if not prompts:
        prompts = await _default_prompts(session, episode)

    planned = [_PlannedShot("image", prompt=p, description=p) for p in prompts]
    planned.append(
        _PlannedShot(
            "tts",
            description="Closing narration",
            text=_narration_text(prompts, episode),
            voice=settings.tts_provider_voice,
        )
    )

    # Persist in order. Image shots chain previous→next; the narration depends on
    # every visual shot. Preserved (approved) shots keep their indices below the
    # new ones is not required — we re-index the new plan starting after them.
    start_index = max((s.index for s in preserved), default=-1) + 1
    new_shots: list[Shot] = []
    image_ids: list[uuid.UUID] = []
    prev_id: uuid.UUID | None = None

    for offset, item in enumerate(planned):
        if item.kind == "tts":
            depends_on = list(image_ids)
        else:
            depends_on = [prev_id] if prev_id is not None else []
        shot = Shot(
            episode_id=episode_id,
            index=start_index + offset,
            description=item.description,
            inputs=item.inputs(),
            depends_on=depends_on,
            status="pending",
        )
        session.add(shot)
        await session.flush()  # assign shot.id
        new_shots.append(shot)
        if item.kind == "image":
            image_ids.append(shot.id)
            prev_id = shot.id

    await session.flush()

    all_shots = preserved + new_shots
    # Validate the persisted graph is acyclic before returning (downstream relies
    # on this; raises CycleError if a bug introduced a cycle).
    deps = {s.id: list(s.depends_on or []) for s in all_shots}
    topo_order(deps)

    summary = _summary(sorted(all_shots, key=lambda s: s.index))
    await pub.emit(EventType.PRODUCTION_STAGE, stage="plan", count=summary["count"])
    return summary


def _summary(shots: list) -> dict:
    return {
        "shots": [
            {
                "id": str(s.id),
                "index": s.index,
                "kind": (s.inputs or {}).get("kind", "image"),
                "depends_on": [str(d) for d in (s.depends_on or [])],
            }
            for s in shots
        ],
        "count": len(shots),
    }


async def run_plan_job(episode_id: uuid.UUID) -> None:
    """Background entrypoint: own session, commit on success, roll back on error.

    Mirrors ``media/produce.py:run_produce_job`` — invoked via FastAPI
    BackgroundTasks; progress streams over Redis on ``episode:{id}``.
    """
    from chronocanvas.db.engine import async_session

    async with async_session() as session:
        try:
            await plan_shots(session, episode_id)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("plan job failed (episode=%s)", episode_id)
