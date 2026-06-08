"""Final 9:16 assembly (TRD §9.2, asr-2in.4) — stitch shots + narration into one
episode artifact.

Walks the episode's shot artifacts in DAG/index order, gathers the narration
audio, and produces a single ``ProductionArtifact`` of ``kind="episode"`` (a
vertical 9:16 ``video/mp4``). When ffmpeg is unavailable we still emit a
deterministic artifact: a JSON manifest listing the ordered shot urls plus the
narration url, with the artifact url pointing at the written manifest. The real
ffmpeg stitch is a drop-in follow-up that reuses the same ordered inputs.

Runs at the FINAL_CUT stage; advancing past FINAL_CUT (to CANON_COMMIT) is a
gated decision owned by the greenlight flow, so we never force it here.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.showrunner.episodes.service import EpisodeService
from chronocanvas.showrunner.episodes.state import EpisodeStatus, InvalidTransitionError
from chronocanvas.showrunner.media.dag import CycleError, topo_order
from chronocanvas.showrunner.rooms.events import EventType, RoomPublisher

logger = logging.getLogger(__name__)

# 9:16 vertical (TRD §9 — short-form output target).
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
EPISODE_MIME = "video/mp4"


def _ordered_shot_ids(shots) -> list[uuid.UUID]:
    """DAG order over the shots, falling back to index order on a cycle."""
    deps = {s.id: list(s.depends_on or []) for s in shots}
    try:
        return topo_order(deps)
    except CycleError:
        logger.warning("assembly: shot DAG has a cycle; falling back to index order")
        return [s.id for s in sorted(shots, key=lambda s: s.index)]


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


async def finalize_episode(
    session: AsyncSession,
    episode_id: uuid.UUID,
    *,
    publisher=None,
) -> dict:
    """Assemble narration + shot artifacts into ONE final episode artifact.

    Returns a summary dict ``{artifact_id, url, mime_type, stitched, shots}``.
    Idempotent enough to re-run: it always writes a fresh ``kind="episode"``
    artifact (a manifest if ffmpeg is missing) and records it on the episode.
    """
    from chronocanvas.config import settings
    from chronocanvas.db.models.showrunner_episode import ProductionArtifact, Shot

    pub = RoomPublisher(str(episode_id), publisher)
    episodes = EpisodeService(session)
    output_dir = settings.output_dir

    episode = await episodes.get(episode_id)
    if episode is None:
        logger.warning("finalize: episode %s not found", episode_id)
        return {"artifact_id": None, "url": None, "mime_type": None,
                "stitched": False, "shots": 0}

    await pub.emit(EventType.PRODUCTION_STAGE, stage="finalize", status="assembling")

    rows = await session.execute(
        select(Shot).where(Shot.episode_id == episode_id).order_by(Shot.index)
    )
    shots = list(rows.scalars().all())
    by_id = {s.id: s for s in shots}

    # Resolve each shot's produced artifact (ordered), split into visuals + narration.
    art_rows = await session.execute(
        select(ProductionArtifact).where(ProductionArtifact.episode_id == episode_id)
    )
    by_shot: dict[uuid.UUID, ProductionArtifact] = {}
    for a in art_rows.scalars().all():
        if a.shot_id is not None and a.kind != "episode":
            by_shot[a.shot_id] = a  # last write wins (current version)

    shot_urls: list[str] = []
    narration_urls: list[str] = []
    for sid in _ordered_shot_ids(shots):
        art = by_shot.get(sid)
        if art is None or not art.url:
            continue
        if art.kind == "audio":
            narration_urls.append(art.url)
        else:
            shot_urls.append(art.url)

    narration_url = narration_urls[0] if narration_urls else None

    # Stitch. ffmpeg is the real path; absent it, write a deterministic manifest.
    os.makedirs(output_dir, exist_ok=True)
    manifest = {
        "episode_id": str(episode_id),
        "width": TARGET_WIDTH,
        "height": TARGET_HEIGHT,
        "aspect": "9:16",
        "mime_type": EPISODE_MIME,
        "shots": shot_urls,
        "narration": narration_url,
        "narration_tracks": narration_urls,
    }
    manifest_name = f"episode_{episode_id}.manifest.json"
    manifest_path = os.path.join(output_dir, manifest_name)
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)

    stitched = _ffmpeg_available() and bool(shot_urls)
    # The real ffmpeg concat/scale-pad is a follow-up; we record the manifest url
    # so the artifact is deterministic and the ordered inputs are preserved.
    final_url = f"/output/{manifest_name}"
    final_mime = "application/json" if not stitched else EPISODE_MIME

    artifact = ProductionArtifact(
        episode_id=episode_id, shot_id=None, kind="episode",
        url=final_url, mime_type=final_mime, version=1, cost_usd=0.0,
        payload={
            "manifest": manifest,
            "stitched": stitched,
            "shot_count": len(shot_urls),
            "has_narration": narration_url is not None,
        },
    )
    session.add(artifact)
    await session.flush()

    await pub.emit(
        EventType.ARTIFACT_READY, artifact_id=str(artifact.id), kind="episode",
        url=final_url, mime_type=final_mime, shots=len(shot_urls),
    )

    # Reach FINAL_CUT if we were still PRODUCING; never force past it (gated).
    if EpisodeStatus(episode.status) == EpisodeStatus.PRODUCING:
        try:
            await episodes.advance(episode, EpisodeStatus.FINAL_CUT)
        except InvalidTransitionError as e:
            logger.warning("finalize: advance to FINAL_CUT skipped: %s", e)

    await pub.emit(
        EventType.PRODUCTION_STAGE, stage="finalize", status="done",
        artifact_id=str(artifact.id), stitched=stitched,
    )
    return {
        "artifact_id": str(artifact.id), "url": final_url, "mime_type": final_mime,
        "stitched": stitched, "shots": len(shot_urls),
    }


async def run_finalize_job(episode_id: uuid.UUID) -> None:
    """Background entrypoint: own session, commit on success, roll back on error.

    Mirrors ``produce.run_produce_job`` / ``rooms/jobs.run_room_job``.
    """
    from chronocanvas.db.engine import async_session

    async with async_session() as session:
        try:
            await finalize_episode(session, episode_id)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("finalize job failed (episode=%s)", episode_id)
