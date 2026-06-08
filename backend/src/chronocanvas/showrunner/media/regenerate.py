"""Selective regeneration (TRD §9.3) — stale DAG walk + preserve approved.

When one shot changes, mark it and every shot that transitively depends on it as
stale, then regenerate the stale set in dependency order. APPROVED shots are
locked: they are preserved (never re-rendered) even when they sit downstream of a
change. Each regenerated shot keeps its prior artifact (a new ``ProductionArtifact``
is written at ``version+1`` carrying a ``compare`` block of prev-vs-new) so the
Production Desk can diff old against new.

Budget is enforced per node via the reserve→commit protocol (TRD §6.6): we reserve
the estimated cost before calling the provider and commit the actual afterwards. A
``BudgetExceeded`` raised mid-batch stops the run gracefully — already-regenerated
shots stay regenerated; the rest remain stale for a later retry.

Providers are injectable (``providers=``) so tests exercise the full DAG walk with
deterministic fakes and never touch the live registry.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, NamedTuple

from sqlalchemy import select

from chronocanvas.showrunner.cost.budget import BudgetExceeded, BudgetService
from chronocanvas.showrunner.cost.pricing import load_pricing, media_cost
from chronocanvas.showrunner.media.dag import stale_closure, topo_order
from chronocanvas.showrunner.rooms.events import EventType, RoomPublisher

logger = logging.getLogger(__name__)

# Where mock/real providers write produced files (matches the produce service).
_OUTPUT_DIR = "output"


class Providers(NamedTuple):
    """The three media generators, bundled for injection."""

    image: Any
    video: Any
    tts: Any


def _resolve_providers(providers: Providers | None) -> Providers:
    """Lazily pull the registry getters when no providers were injected so tests
    never need the registry module (and the live registry stays a runtime concern)."""
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


async def _generate(providers: Providers, inputs: dict) -> Any:
    """Dispatch to the provider matching ``inputs.kind`` and return its MediaArtifact."""
    kind = (inputs or {}).get("kind", "image")
    if kind == "video":
        return await providers.video.generate_video(
            (inputs or {}).get("prompt", ""),
            output_dir=_OUTPUT_DIR,
            seconds=float((inputs or {}).get("seconds", 8.0)),
            image_url=(inputs or {}).get("image_url"),
        )
    if kind == "tts":
        return await providers.tts.synthesize(
            (inputs or {}).get("text", ""),
            output_dir=_OUTPUT_DIR,
            voice=(inputs or {}).get("voice"),
        )
    return await providers.image.generate_image(
        (inputs or {}).get("prompt", ""), output_dir=_OUTPUT_DIR
    )


async def _max_version(session, shot_id: uuid.UUID) -> int:
    """Highest existing artifact version for a shot (0 if none)."""
    from chronocanvas.db.models.showrunner_episode import ProductionArtifact

    rows = await session.execute(
        select(ProductionArtifact.version).where(ProductionArtifact.shot_id == shot_id)
    )
    versions = [v for (v,) in rows.all()]
    return max(versions) if versions else 0


async def regenerate_shot(
    session,
    episode_id: uuid.UUID,
    shot_id: uuid.UUID,
    *,
    publisher: Any | None = None,
    providers: Providers | None = None,
) -> dict:
    """Regenerate ``shot_id`` and every non-approved shot that depends on it.

    Returns a summary ``{"regenerated": [...], "preserved": [...], "skipped": [...]}``
    of shot ids (as strings).
    """
    from chronocanvas.db.models.showrunner_cost import MediaGeneration
    from chronocanvas.db.models.showrunner_episode import ProductionArtifact, Shot

    pub = publisher if isinstance(publisher, RoomPublisher) else RoomPublisher(
        str(episode_id), publisher=publisher
    )
    providers = _resolve_providers(providers)
    pricing = load_pricing()
    budget = BudgetService(session)

    # 1. Load all shots; build deps; compute the stale closure of the change.
    rows = await session.execute(select(Shot).where(Shot.episode_id == episode_id))
    shots = {s.id: s for s in rows.scalars().all()}
    deps = {sid: list(s.depends_on or []) for sid, s in shots.items()}
    stale_ids = stale_closure(deps, shot_id)

    # 2. Approved shots are locked → preserved; the rest of the closure regenerates.
    preserved = [str(sid) for sid in stale_ids if shots.get(sid) and shots[sid].status == "approved"]
    to_regen = [sid for sid in stale_ids if shots.get(sid) and shots[sid].status != "approved"]

    for sid in to_regen:
        shots[sid].status = "stale"
    await session.flush()
    await pub.emit(
        EventType.PRODUCTION_STAGE,
        stage="regenerate",
        stale=[str(sid) for sid in to_regen],
        preserved=preserved,
    )

    # 3. Regenerate in dependency order (upstream before downstream).
    order = [sid for sid in topo_order(deps) if sid in set(to_regen)]

    regenerated: list[str] = []
    skipped: list[str] = []
    for sid in order:
        shot = shots[sid]
        try:
            # Pre-flight estimate from the unit price for this kind (image=1 unit;
            # video/tts re-priced from actual units after generation).
            kind = (shot.inputs or {}).get("kind", "image")
            _, est_cost = media_cost(kind, 1.0, pricing)
            reservation, _check = await budget.reserve(
                "episode", episode_id, est_cost, job_id=f"regen:{sid}"
            )

            artifact = await _generate(providers, shot.inputs or {})
            unit_price, actual_cost = media_cost(kind, artifact.units, pricing)

            prior = await session.get(ProductionArtifact, shot.artifact_id) if shot.artifact_id else None
            next_version = await _max_version(session, sid) + 1

            new_artifact = ProductionArtifact(
                episode_id=episode_id,
                shot_id=sid,
                kind=artifact.kind,
                url=artifact.url,
                mime_type=artifact.mime_type,
                version=next_version,
                cost_usd=round(actual_cost, 8),
                payload={
                    "provider": artifact.provider,
                    "model": artifact.model,
                    "units": artifact.units,
                    "compare": {
                        "prev_artifact_id": str(prior.id) if prior else None,
                        "prev_url": prior.url if prior else None,
                        "new_url": artifact.url,
                    },
                },
            )
            session.add(new_artifact)
            await session.flush()

            session.add(
                MediaGeneration(
                    episode_id=episode_id,
                    shot_id=sid,
                    kind=artifact.kind,
                    provider=artifact.provider or "",
                    model=artifact.model,
                    units=artifact.units,
                    unit_cost_usd=unit_price,
                    cost_usd=round(actual_cost, 8),
                    duration_ms=artifact.duration_ms,
                    status="ok",
                )
            )

            await budget.commit(reservation.id, round(actual_cost, 8))

            shot.artifact_id = new_artifact.id
            shot.status = "ready"
            await session.flush()

            regenerated.append(str(sid))
            await pub.emit(
                EventType.ARTIFACT_READY,
                shot_id=str(sid),
                artifact_id=str(new_artifact.id),
                version=next_version,
                url=artifact.url,
            )
        except BudgetExceeded as e:
            # Hard cap would break — stop gracefully; remaining shots stay stale.
            await pub.emit(EventType.BUDGET_EXCEEDED, shot_id=str(sid), **e.check.as_error())
            logger.warning("regenerate stopped on budget (episode=%s shot=%s)", episode_id, sid)
            skipped.extend(str(x) for x in order[order.index(sid):] if str(x) not in regenerated)
            break
        except Exception:
            # One shot failing must not abort the batch.
            logger.exception("regenerate failed for shot %s (episode=%s)", sid, episode_id)
            skipped.append(str(sid))

    return {"regenerated": regenerated, "preserved": preserved, "skipped": skipped}


async def run_regenerate_job(episode_id: uuid.UUID, shot_id: uuid.UUID) -> None:
    """Background entrypoint: own session, commit on success, log+rollback on error."""
    from chronocanvas.db.engine import async_session

    async with async_session() as session:
        try:
            await regenerate_shot(session, episode_id, shot_id)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception(
                "regenerate job failed (episode=%s shot=%s)", episode_id, shot_id
            )
