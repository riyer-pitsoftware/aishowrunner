"""Showrunner room + greenlight API (PRD §8, TRD §8).

Rooms run as background jobs (return episode id immediately; progress streams via
Redis). Greenlight gates enforce budget at the episode gate (TRD §6.6) and record
immutable decisions with frozen dissent (TRD §8.3).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.db.engine import get_session
from chronocanvas.showrunner.cost.budget import BudgetExceeded, BudgetService
from chronocanvas.showrunner.episodes.service import EpisodeService
from chronocanvas.showrunner.episodes.state import EpisodeStatus
from chronocanvas.showrunner.rooms.gates import GateService
from chronocanvas.showrunner.rooms.jobs import run_room_job

router = APIRouter(tags=["rooms"])


class StoryRoomRequest(BaseModel):
    title: str | None = None
    premise: str | None = None
    task: str = "Develop the next episode: propose 2-3 branch directions."


class RoomRunRequest(BaseModel):
    task: str = "Convert the approved plan into production artifacts."


class GreenlightRequest(BaseModel):
    verdict: str  # approved|defer|reduce|kill
    actor: str | None = None
    rationale: str | None = None
    decision_id: str | None = None
    chosen_option_id: uuid.UUID | None = None
    estimate_usd: float = 0.0  # reserved at the episode gate


@router.post("/series/{series_id}/story-room", status_code=202)
async def convene_story_room(
    series_id: uuid.UUID,
    body: StoryRoomRequest,
    background: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    from chronocanvas.showrunner.series.service import CanonService

    if await CanonService(session).get_series(series_id) is None:
        raise HTTPException(status_code=404, detail="series not found")
    svc = EpisodeService(session)
    episode = await svc.create_episode(series_id, title=body.title, premise=body.premise)
    await session.commit()
    background.add_task(
        run_room_job, series_id, episode.id, "story_room", body.task,
        advance_to=EpisodeStatus.STORY_ROOM.value,
    )
    return {"episode_id": str(episode.id), "status": "story_room", "accepted": True}


@router.post("/episodes/{episode_id}/production-desk", status_code=202)
async def convene_production_desk(
    episode_id: uuid.UUID,
    body: RoomRunRequest,
    background: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    episode = await EpisodeService(session).get(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")
    background.add_task(
        run_room_job, episode.series_id, episode_id, "production_desk", body.task,
    )
    return {"episode_id": str(episode_id), "accepted": True}


@router.get("/episodes/{episode_id}")
async def get_episode(episode_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    episode = await EpisodeService(session).get(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")
    return EpisodeService.describe(episode)


@router.get("/episodes/{episode_id}/contributions")
async def get_contributions(episode_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    from chronocanvas.db.models.showrunner_room import SkillContribution

    rows = await session.execute(
        select(SkillContribution).where(SkillContribution.episode_id == episode_id)
    )
    return [
        {
            "id": str(r.id), "room": r.room, "skill_name": r.skill_name,
            "stance": r.stance, "summary": r.summary,
            "recommendations": r.recommendations, "risks": r.risks,
            "fields": r.fields, "decision_id": r.decision_id,
        }
        for r in rows.scalars().all()
    ]


@router.get("/episodes/{episode_id}/disagreements")
async def get_disagreements(episode_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    from chronocanvas.db.models.showrunner_room import SpecialistDisagreement

    rows = await session.execute(
        select(SpecialistDisagreement).where(SpecialistDisagreement.episode_id == episode_id)
    )
    return [
        {"id": str(r.id), "axis": r.axis, "stances": r.stances,
         "detail": r.detail, "resolved": r.resolved, "decision_id": r.decision_id}
        for r in rows.scalars().all()
    ]


@router.post("/episodes/{episode_id}/greenlights/{gate}")
async def post_greenlight(
    episode_id: uuid.UUID,
    gate: str,
    body: GreenlightRequest,
    session: AsyncSession = Depends(get_session),
):
    if gate not in ("branch", "episode", "final"):
        raise HTTPException(status_code=400, detail="gate must be branch|episode|final")
    episode = await EpisodeService(session).get(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")

    approving = (body.verdict or "").lower() in {"approved", "ship", "approve"}
    # Budget enforcement at the episode gate (TRD §6.6)
    if gate == "episode" and approving and body.estimate_usd > 0:
        try:
            await BudgetService(session).reserve(
                "episode", episode_id, body.estimate_usd, job_id=f"greenlight:{episode_id}"
            )
        except BudgetExceeded as e:
            raise HTTPException(status_code=409, detail=e.check.as_error())

    try:
        gate_row = await GateService(session).record_gate(
            episode, gate=gate, verdict=body.verdict, actor=body.actor,
            chosen_option_id=body.chosen_option_id, rationale=body.rationale,
            decision_id=body.decision_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await session.commit()
    return {
        "gate_id": str(gate_row.id), "gate": gate, "verdict": body.verdict,
        "status": episode.status,
    }
