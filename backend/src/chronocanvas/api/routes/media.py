"""Media Production API (TRD §9).

Produce / finalize / regenerate run as background jobs (return the episode id
immediately; progress streams over Redis on ``episode:{id}``). Read endpoints
expose the shot DAG and produced artifacts for the Production Desk UI.

Budget is enforced inside the produce/regenerate jobs (reserve→commit per node,
TRD §6.6); the synchronous handlers only validate state and dispatch.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.db.engine import get_session
from chronocanvas.showrunner.episodes.service import EpisodeService

router = APIRouter(tags=["media"])


@router.post("/episodes/{episode_id}/produce", status_code=202)
async def produce_episode(
    episode_id: uuid.UUID,
    background: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Generate all shots for an episode whose plan was greenlit."""
    episode = await EpisodeService(session).get(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")

    from chronocanvas.showrunner.media.produce import run_produce_job

    background.add_task(run_produce_job, episode_id)
    return {"episode_id": str(episode_id), "accepted": True, "stage": "produce"}


@router.post("/episodes/{episode_id}/plan-shots", status_code=202)
async def plan_shots(
    episode_id: uuid.UUID,
    background: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Derive the Shot DAG from the episode's approved plan (TRD §9.1).

    This is the stage that *creates* the shots ``produce`` later walks.
    """
    episode = await EpisodeService(session).get(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")

    from chronocanvas.showrunner.media.planner import run_plan_job

    background.add_task(run_plan_job, episode_id)
    return {"episode_id": str(episode_id), "accepted": True, "stage": "plan"}


@router.post("/episodes/{episode_id}/finalize", status_code=202)
async def finalize_episode(
    episode_id: uuid.UUID,
    background: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Assemble narration + shots into the final vertical 9:16 episode artifact."""
    episode = await EpisodeService(session).get(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")

    from chronocanvas.showrunner.media.assembly import run_finalize_job

    background.add_task(run_finalize_job, episode_id)
    return {"episode_id": str(episode_id), "accepted": True, "stage": "finalize"}


@router.post("/episodes/{episode_id}/shots/{shot_id}/regenerate", status_code=202)
async def regenerate_shot(
    episode_id: uuid.UUID,
    shot_id: uuid.UUID,
    background: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Selectively regenerate one shot and everything that depends on it,
    preserving approved assets (TRD §9.3)."""
    from chronocanvas.db.models.showrunner_episode import Shot

    shot = await session.get(Shot, shot_id)
    if shot is None or shot.episode_id != episode_id:
        raise HTTPException(status_code=404, detail="shot not found for episode")

    from chronocanvas.showrunner.media.regenerate import run_regenerate_job

    background.add_task(run_regenerate_job, episode_id, shot_id)
    return {"episode_id": str(episode_id), "shot_id": str(shot_id), "accepted": True}


@router.get("/episodes/{episode_id}/shots")
async def list_shots(episode_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    from chronocanvas.db.models.showrunner_episode import Shot

    rows = await session.execute(
        select(Shot).where(Shot.episode_id == episode_id).order_by(Shot.index)
    )
    return [
        {
            "id": str(s.id),
            "index": s.index,
            "description": s.description,
            "inputs": s.inputs,
            "depends_on": [str(d) for d in (s.depends_on or [])],
            "status": s.status,
            "artifact_id": str(s.artifact_id) if s.artifact_id else None,
        }
        for s in rows.scalars().all()
    ]


@router.get("/episodes/{episode_id}/artifacts")
async def list_artifacts(episode_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    from chronocanvas.db.models.showrunner_episode import ProductionArtifact

    rows = await session.execute(
        select(ProductionArtifact)
        .where(ProductionArtifact.episode_id == episode_id)
        .order_by(ProductionArtifact.created_at)
    )
    return [
        {
            "id": str(a.id),
            "shot_id": str(a.shot_id) if a.shot_id else None,
            "kind": a.kind,
            "url": a.url,
            "mime_type": a.mime_type,
            "version": a.version,
            "cost_usd": a.cost_usd,
            "payload": a.payload,
        }
        for a in rows.scalars().all()
    ]
