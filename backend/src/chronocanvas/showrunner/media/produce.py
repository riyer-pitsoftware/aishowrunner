"""Plan → media generation (TRD §9.2) — walk the Shot DAG and produce artifacts.

Generation is the authoritative budget-enforcement point (reserve→commit per
node, TRD §6.6): each shot estimates its cost, reserves it, generates via the
media provider, then commits the actual cost recomputed from the artifact's
billable ``units``. A persistent media-cost ledger row (``MediaGeneration``) and
a ``ProductionArtifact`` are written per shot, and progress streams over Redis.

Providers are resolved lazily from ``media.registry`` so this module imports
cleanly without DashScope configured; tests inject a ``Providers`` bundle of
fakes and never touch the registry.
"""

from __future__ import annotations

import logging
import uuid
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.showrunner.cost.budget import BudgetExceeded, BudgetService
from chronocanvas.showrunner.cost.pricing import load_pricing, media_cost
from chronocanvas.showrunner.episodes.service import EpisodeService
from chronocanvas.showrunner.episodes.state import EpisodeStatus, InvalidTransitionError
from chronocanvas.showrunner.media.dag import CycleError, topo_order
from chronocanvas.showrunner.rooms.events import EventType, RoomPublisher

logger = logging.getLogger(__name__)

# Default video length (seconds) when a shot's inputs omit it.
DEFAULT_VIDEO_SECONDS = 8.0
BUDGET_SCOPE = "episode"


class Providers(NamedTuple):
    """Injectable media provider bundle (tests pass fakes)."""

    image: object
    video: object
    tts: object


def _resolve_providers(providers: Providers | None) -> Providers:
    """Return the injected providers, else lazily resolve the registry getters.

    The registry import is deferred so this module (and its tests) load without
    a DashScope key or the provider implementations being importable.
    """
    if providers is not None:
        return providers
    from chronocanvas.showrunner.media.registry import (
        get_image_provider,
        get_tts_provider,
        get_video_provider,
    )

    return Providers(
        image=get_image_provider(),
        video=get_video_provider(),
        tts=get_tts_provider(),
    )


def _expected_units(kind: str, inputs: dict) -> float:
    """Pre-generation units guess for the budget reservation.

    Recomputed exactly from the returned artifact before commit; this only needs
    to be a reasonable upper estimate so the reserve→commit protocol holds.
    """
    if kind == "video":
        try:
            return float(inputs.get("seconds") or DEFAULT_VIDEO_SECONDS)
        except (TypeError, ValueError):
            return DEFAULT_VIDEO_SECONDS
    if kind == "tts":
        return float(len(inputs.get("text") or ""))
    return 1.0  # image (and any unknown kind) → one unit


async def _generate(providers: Providers, kind: str, inputs: dict, output_dir: str):
    """Dispatch to the matching provider, returning a MediaArtifact."""
    if kind == "video":
        seconds = _expected_units("video", inputs)
        return await providers.video.generate_video(
            inputs.get("prompt") or inputs.get("text") or "",
            output_dir=output_dir,
            seconds=seconds,
            image_url=inputs.get("image_url"),
        )
    if kind == "tts":
        return await providers.tts.synthesize(
            inputs.get("text") or "",
            output_dir=output_dir,
            voice=inputs.get("voice"),
        )
    # image (default)
    return await providers.image.generate_image(
        inputs.get("prompt") or inputs.get("text") or "",
        output_dir=output_dir,
    )


def _artifact_kind(media_kind: str) -> str:
    """Map a generation kind to a ProductionArtifact kind."""
    if media_kind == "tts":
        return "audio"
    if media_kind == "video":
        return "video"
    return "image"


async def produce_episode(
    session: AsyncSession,
    episode_id: uuid.UUID,
    *,
    publisher=None,
    providers: Providers | None = None,
) -> dict:
    """Generate every shot for ``episode_id`` in dependency order.

    Returns a summary dict ``{produced, skipped, failed, stopped}``. One shot's
    failure is isolated (logged, marked failed) and does not abort the run; a
    hard budget breach stops the run gracefully after emitting BUDGET_EXCEEDED.
    """
    from chronocanvas.config import settings
    from chronocanvas.db.models.showrunner_cost import MediaGeneration
    from chronocanvas.db.models.showrunner_episode import ProductionArtifact, Shot

    pub = RoomPublisher(str(episode_id), publisher)
    providers = _resolve_providers(providers)
    pricing = load_pricing()
    budget = BudgetService(session)
    episodes = EpisodeService(session)
    output_dir = settings.output_dir

    episode = await episodes.get(episode_id)
    if episode is None:
        logger.warning("produce: episode %s not found", episode_id)
        return {"produced": 0, "skipped": 0, "failed": 0, "stopped": True}

    # EPISODE_GREENLIGHT → PRODUCING (idempotent; tolerate already-past).
    try:
        await episodes.advance(episode, EpisodeStatus.PRODUCING)
    except InvalidTransitionError as e:
        logger.warning("produce: advance to PRODUCING skipped: %s", e)

    rows = await session.execute(
        select(Shot).where(Shot.episode_id == episode_id).order_by(Shot.index)
    )
    shots = list(rows.scalars().all())
    by_id = {s.id: s for s in shots}
    deps = {s.id: list(s.depends_on or []) for s in shots}

    try:
        order = topo_order(deps)
    except CycleError:
        logger.exception("produce: shot DAG has a cycle (episode=%s)", episode_id)
        await pub.emit(EventType.TERMINAL, stage="produce", ok=False, reason="cycle")
        return {"produced": 0, "skipped": 0, "failed": 0, "stopped": True}

    produced = skipped = failed = 0
    stopped = False

    for shot_id in order:
        shot = by_id.get(shot_id)
        if shot is None:  # dangling dependency reference — nothing to generate
            continue
        if shot.status == "approved":
            skipped += 1
            continue

        inputs = shot.inputs or {}
        kind = inputs.get("kind", "image")
        shot.status = "generating"
        await session.flush()
        await pub.emit(
            EventType.PRODUCTION_STAGE, shot_id=str(shot.id), index=shot.index,
            kind=kind, status="generating",
        )

        # Reserve an estimate before generating (reserve→commit, TRD §6.6).
        est_units = _expected_units(kind, inputs)
        _, est_cost = media_cost(kind, est_units, pricing)
        try:
            reservation, _check = await budget.reserve(
                BUDGET_SCOPE, episode_id, est_cost, job_id=f"produce:{shot.id}",
            )
        except BudgetExceeded as exc:
            logger.warning(
                "produce: budget exceeded at shot %s (episode=%s)", shot.id, episode_id
            )
            shot.status = "pending"
            await session.flush()
            await pub.emit(
                EventType.BUDGET_EXCEEDED, shot_id=str(shot.id), **exc.check.as_error()
            )
            stopped = True
            break

        try:
            artifact = await _generate(providers, kind, inputs, output_dir)
        except Exception:
            logger.exception("produce: shot %s generation failed", shot.id)
            await budget.release(reservation.id)
            shot.status = "failed"
            await session.flush()
            session.add(
                MediaGeneration(
                    episode_id=episode_id, shot_id=shot.id, kind=kind,
                    provider="", model=None, units=0.0,
                    unit_cost_usd=0.0, cost_usd=0.0, duration_ms=0.0, status="failed",
                )
            )
            await session.flush()
            failed += 1
            continue

        # Recompute the authoritative cost from the artifact's billable units.
        unit_price, actual_cost = media_cost(kind, artifact.units, pricing)
        await budget.commit(reservation.id, actual_cost)

        prod = ProductionArtifact(
            episode_id=episode_id, shot_id=shot.id, kind=_artifact_kind(kind),
            url=artifact.url, mime_type=artifact.mime_type, version=1,
            cost_usd=actual_cost,
            payload={
                "provider": artifact.provider, "model": artifact.model,
                "units": artifact.units, "width": artifact.width,
                "height": artifact.height, "duration_ms": artifact.duration_ms,
                "media_kind": kind, **(artifact.meta or {}),
            },
        )
        session.add(prod)
        await session.flush()

        session.add(
            MediaGeneration(
                episode_id=episode_id, shot_id=shot.id, kind=kind,
                provider=artifact.provider, model=artifact.model, units=artifact.units,
                unit_cost_usd=unit_price, cost_usd=actual_cost,
                duration_ms=artifact.duration_ms, status="ok",
            )
        )

        shot.artifact_id = prod.id
        shot.status = "ready"
        await session.flush()
        produced += 1
        await pub.emit(
            EventType.ARTIFACT_READY, shot_id=str(shot.id), artifact_id=str(prod.id),
            kind=_artifact_kind(kind), url=artifact.url, cost_usd=round(actual_cost, 6),
        )

    # Continuity eval runs only after a clean full pass; non-blocking (TRD §9.4).
    all_ready = not stopped and all(
        by_id[sid].status in ("ready", "approved") for sid in order if sid in by_id
    )
    if all_ready and order:
        try:
            from chronocanvas.showrunner.media.continuity import maybe_run_continuity

            await maybe_run_continuity(session, episode_id, publisher=publisher)
        except Exception:  # eval is non-blocking (TRD §9.4)
            logger.warning("continuity eval skipped", exc_info=True)

        # PRODUCING → FINAL_CUT once every shot is done.
        try:
            await episodes.advance(episode, EpisodeStatus.FINAL_CUT)
        except InvalidTransitionError as e:
            logger.warning("produce: advance to FINAL_CUT skipped: %s", e)

    await pub.emit(
        EventType.PRODUCTION_STAGE, stage="produce", status="done",
        produced=produced, skipped=skipped, failed=failed, stopped=stopped,
    )
    return {"produced": produced, "skipped": skipped, "failed": failed, "stopped": stopped}


async def run_produce_job(episode_id: uuid.UUID) -> None:
    """Background entrypoint: own session, commit on success, roll back on error.

    Mirrors ``rooms/jobs.run_room_job`` — invoked via FastAPI BackgroundTasks;
    progress streams over Redis on ``episode:{id}`` (TRD §4.1).
    """
    from chronocanvas.db.engine import async_session

    async with async_session() as session:
        try:
            await produce_episode(session, episode_id)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("produce job failed (episode=%s)", episode_id)
