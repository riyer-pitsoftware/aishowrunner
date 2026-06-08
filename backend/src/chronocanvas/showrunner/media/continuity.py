"""Continuity eval pass (TRD §9.4, asr-2in.5) — a critic-tier check over the
finished episode that surfaces continuity contradictions in the Production Desk.

This is a *critic*, not a gate: a low score is a WARNING (a "concern"
contribution), never an auto-block. The pass is default-ON, disabled with
``EVAL_ENABLED=false``, and is invoked defensively by ``produce_episode`` after
a clean full generation pass. It must never raise back into produce — every
failure path (disabled, budget breach, scorer error) degrades to a non-blocking
skip and the episode's lifecycle state is left untouched.

The scorer is injectable for tests; the default scorer calls the critic-tier
LLM (``settings.eval_model`` — a non-coder Qwen model) in JSON mode and parses
its result. The eval call itself costs tokens, so it is reserve→commit'd against
the episode budget like any other production spend (TRD §6.6).
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.showrunner.cost.budget import (
    BudgetExceeded,
    BudgetService,
    estimate_production,
)
from chronocanvas.showrunner.rooms.events import EventType, RoomPublisher

logger = logging.getLogger(__name__)

# Score >= this is "support" (clean); below is "concern" (a continuity warning).
PASS_THRESHOLD = 0.7
BUDGET_SCOPE = "episode"
ROOM = "production_desk"
SKILL_NAME = "continuity-eval"

# Type of the injectable scorer seam.
Scorer = Callable[[str], Awaitable[dict]]


def _build_prompt(facts: list[str], shots: list[str]) -> str:
    """A short critic prompt: known canon + produced shots → contradictions + score."""
    facts_block = "\n".join(f"- {f}" for f in facts) or "- (no canon facts on record)"
    shots_block = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(shots)) or "(no shots)"
    return (
        "You are a continuity supervisor reviewing a finished episode for "
        "contradictions against the series canon and across its own shots.\n\n"
        "Known canon facts:\n"
        f"{facts_block}\n\n"
        "Produced shots, in order:\n"
        f"{shots_block}\n\n"
        "List any continuity contradictions (character, wardrobe, time-of-day, "
        "props, geography, established facts). Then score overall continuity from "
        "0.0 (badly broken) to 1.0 (flawless).\n"
        'Respond as JSON: {"score": <float 0..1>, "issues": [<string>, ...], '
        '"summary": <one-sentence verdict>}.'
    )


async def _gather_context(
    session: AsyncSession, episode_id: uuid.UUID
) -> tuple[list[str], list[str]]:
    """Collect canon facts for the episode's series + produced shot descriptions.

    Kept deliberately simple and defensive: any missing series/canon degrades to
    an empty fact list rather than raising.
    """
    from chronocanvas.db.models.showrunner_episode import (
        Episode,
        ProductionArtifact,
        Shot,
    )

    facts: list[str] = []
    episode = await session.get(Episode, episode_id)
    if episode is not None and episode.series_id is not None:
        try:
            from chronocanvas.showrunner.series.service import CanonService

            canon = await CanonService(session).get_canon(episode.series_id)
            facts = _flatten_canon(canon)
        except Exception:  # canon is best-effort context, never load-bearing
            logger.debug("continuity: canon read failed", exc_info=True)

    # Produced shot descriptions: prefer the shot's own description, fall back to
    # its prompt input, and append the latest artifact url for grounding.
    shot_rows = await session.execute(
        select(Shot).where(Shot.episode_id == episode_id).order_by(Shot.index)
    )
    shots = list(shot_rows.scalars().all())

    art_rows = await session.execute(
        select(ProductionArtifact).where(ProductionArtifact.episode_id == episode_id)
    )
    latest_url: dict[uuid.UUID, str] = {}
    latest_ver: dict[uuid.UUID, int] = {}
    for art in art_rows.scalars().all():
        if art.shot_id is None:
            continue
        if art.version >= latest_ver.get(art.shot_id, -1):
            latest_ver[art.shot_id] = art.version
            latest_url[art.shot_id] = art.url or ""

    descriptions: list[str] = []
    for shot in shots:
        inputs = shot.inputs or {}
        text = shot.description or inputs.get("prompt") or inputs.get("text") or "(shot)"
        url = latest_url.get(shot.id)
        descriptions.append(f"{text} [{url}]" if url else str(text))

    return facts, descriptions


def _flatten_canon(canon: dict | None) -> list[str]:
    """Render a folded canon dict into short human-readable fact strings."""
    facts: list[str] = []
    if not isinstance(canon, dict):
        return facts
    for section, value in canon.items():
        if isinstance(value, dict):
            for key, detail in value.items():
                facts.append(f"{section}.{key}: {detail}")
        elif isinstance(value, list):
            for item in value:
                facts.append(f"{section}: {item}")
        else:
            facts.append(f"{section}: {value}")
    return facts


def _default_scorer(model: str) -> Scorer:
    """Build a scorer that calls the critic-tier LLM in JSON mode.

    Honors the critic caveat: a non-coder Qwen model (``settings.eval_model``).
    Any failure is allowed to propagate to ``maybe_run_continuity``, which treats
    it as a non-blocking skip.
    """

    async def scorer(prompt: str) -> dict:
        from chronocanvas.llm.base import TaskType
        from chronocanvas.llm.router import get_llm_router
        from chronocanvas.showrunner.cost.pricing import split_model

        provider_name, _ = split_model(model)
        router = get_llm_router()
        response = await router.generate(
            prompt,
            task_type=TaskType.VALIDATION,
            json_mode=True,
            temperature=0.0,
            provider_override=provider_name if provider_name in router.providers else None,
        )
        data = json.loads(response.content)
        return {
            "score": float(data.get("score", 0.0)),
            "issues": list(data.get("issues", []) or []),
            "summary": str(data.get("summary", "")),
        }

    return scorer


async def maybe_run_continuity(
    session: AsyncSession,
    episode_id: uuid.UUID,
    *,
    publisher=None,
    scorer: Scorer | None = None,
) -> dict | None:
    """Run the continuity eval for ``episode_id`` if eval is enabled (TRD §9.4).

    Returns ``None`` when eval is disabled. Otherwise returns
    ``{score, passed, issues, summary, contribution_id}``. NEVER raises: every
    failure (budget breach, scorer/LLM error) degrades to a non-blocking skip and
    the episode lifecycle is left untouched. A failing score is a WARNING, written
    as a "concern" contribution — it is never an auto-block.
    """
    from chronocanvas.config import settings

    # 1. Gate on eval_enabled (read at call time).
    if not settings.eval_enabled:
        return None

    pub = RoomPublisher(str(episode_id), publisher)

    # 2. Budget-gate the eval call (it costs tokens). Reserve a small estimate.
    budget = BudgetService(session)
    est_cost = estimate_production(num_skill_calls=1, skill_model=settings.eval_model)
    job_id = f"continuity:{episode_id}"
    try:
        reservation, _check = await budget.reserve(
            BUDGET_SCOPE, episode_id, est_cost, job_id=job_id
        )
    except BudgetExceeded as exc:
        logger.warning("continuity: budget exceeded for episode %s", episode_id)
        await pub.emit(
            EventType.BUDGET_WARNING, stage="continuity", **exc.check.as_error()
        )
        return None

    # 3. Gather context + score. Any error here is non-blocking: release the
    #    reservation and return a skip note rather than raising into produce.
    try:
        facts, shots = await _gather_context(session, episode_id)
        prompt = _build_prompt(facts, shots)
        run = scorer if scorer is not None else _default_scorer(settings.eval_model)
        result = await run(prompt)
        score = float(result.get("score", 0.0))
        issues = list(result.get("issues", []) or [])
        summary = str(result.get("summary", "")) or "Continuity eval complete."
    except Exception:
        logger.warning("continuity: eval skipped (scorer error)", exc_info=True)
        await budget.release(reservation.id)
        await pub.emit(
            EventType.PRODUCTION_STAGE, stage="continuity", skipped=True,
            note="scorer error",
        )
        return {"skipped": True, "note": "scorer error"}

    # Commit the (estimated) eval cost — token counts aren't returned by the
    # harness, so the reservation estimate stands in as the billed amount.
    await budget.commit(reservation.id, est_cost)

    passed = score >= PASS_THRESHOLD
    # A low score is a CONCERN (warning), never "block" (TRD §9.4).
    stance = "support" if passed else "concern"

    # 4. Persist a Production Desk contribution so the existing feed surfaces it.
    from chronocanvas.db.models.showrunner_room import SkillContribution

    contribution = SkillContribution(
        episode_id=episode_id,
        room=ROOM,
        skill_name=SKILL_NAME,
        stance=stance,
        summary=summary,
        recommendations=[],
        risks=issues,
        fields={"score": round(score, 4), "passed": passed, "issues": issues},
    )
    session.add(contribution)
    await session.flush()

    # 5. Emit a progress event for the live Production Desk.
    await pub.emit(
        EventType.PRODUCTION_STAGE, stage="continuity", score=round(score, 4),
        passed=passed,
    )

    # 6. Return the structured verdict.
    return {
        "score": score,
        "passed": passed,
        "issues": issues,
        "summary": summary,
        "contribution_id": str(contribution.id),
    }
