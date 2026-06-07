"""Cost & Budgeting API (TRD §6.6, §11).

Budgets for series/episode, the priced cost rollup, a deterministic pre-flight
estimate, and the skill-invocation ledger view. Over-hard-cap returns
``409 budget_exceeded``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.api.schemas.cost import (
    BudgetOut,
    BudgetUpdate,
    CostRollupOut,
    EstimateOut,
    EstimateRequest,
)
from chronocanvas.config import settings
from chronocanvas.db.engine import get_session
from chronocanvas.showrunner.cost import (
    BudgetService,
    episode_cost_rollup,
    estimate_production,
    evaluate,
)

router = APIRouter(tags=["cost"])


def _default_limit(scope: str) -> float:
    return (
        settings.budget_series_limit_usd
        if scope == "series"
        else settings.budget_episode_limit_usd
    )


def _to_out(b) -> BudgetOut:
    available = (b.limit_usd - b.spent_usd - b.reserved_usd) if b.limit_usd > 0 else -1.0
    return BudgetOut(
        scope=b.scope, scope_id=b.scope_id, limit_usd=b.limit_usd, soft_pct=b.soft_pct,
        hard_behavior=b.hard_behavior, spent_usd=b.spent_usd, reserved_usd=b.reserved_usd,
        available_usd=round(available, 6),
    )


async def _get_budget(session, scope: str, scope_id: uuid.UUID):
    svc = BudgetService(session)
    return await svc.get_or_create(
        scope, scope_id,
        limit_usd=_default_limit(scope),
        soft_pct=settings.budget_soft_pct,
        hard_behavior=settings.budget_hard_behavior,
    )


async def _update_budget(session, scope, scope_id, body: BudgetUpdate):
    b = await _get_budget(session, scope, scope_id)
    if body.limit_usd is not None:
        b.limit_usd = body.limit_usd
    if body.soft_pct is not None:
        b.soft_pct = body.soft_pct
    if body.hard_behavior is not None:
        b.hard_behavior = body.hard_behavior
    await session.commit()
    return b


@router.get("/series/{series_id}/budget", response_model=BudgetOut)
async def get_series_budget(series_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    b = await _get_budget(session, "series", series_id)
    await session.commit()
    return _to_out(b)


@router.put("/series/{series_id}/budget", response_model=BudgetOut)
async def put_series_budget(
    series_id: uuid.UUID, body: BudgetUpdate, session: AsyncSession = Depends(get_session)
):
    return _to_out(await _update_budget(session, "series", series_id, body))


@router.get("/episodes/{episode_id}/budget", response_model=BudgetOut)
async def get_episode_budget(episode_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    b = await _get_budget(session, "episode", episode_id)
    await session.commit()
    return _to_out(b)


@router.put("/episodes/{episode_id}/budget", response_model=BudgetOut)
async def put_episode_budget(
    episode_id: uuid.UUID, body: BudgetUpdate, session: AsyncSession = Depends(get_session)
):
    return _to_out(await _update_budget(session, "episode", episode_id, body))


@router.get("/episodes/{episode_id}/cost", response_model=CostRollupOut)
async def get_episode_cost(episode_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return await episode_cost_rollup(session, episode_id)


@router.post("/episodes/{episode_id}/estimate", response_model=EstimateOut)
async def post_estimate(
    episode_id: uuid.UUID, body: EstimateRequest, session: AsyncSession = Depends(get_session)
):
    estimate = estimate_production(
        num_skill_calls=body.num_skill_calls, num_images=body.num_images,
        num_video_seconds=body.num_video_seconds, num_tts_chars=body.num_tts_chars,
        skill_model=body.skill_model,
    )
    b = await _get_budget(session, "episode", episode_id)
    await session.commit()
    check = evaluate(
        b.limit_usd, b.spent_usd, b.reserved_usd, estimate,
        soft_pct=b.soft_pct, hard_behavior=b.hard_behavior,
    )
    return EstimateOut(
        estimate_usd=estimate, outcome=check.outcome,
        projected_usd=round(check.projected, 6), limit_usd=b.limit_usd,
    )


@router.get("/episodes/{episode_id}/invocations")
async def list_invocations(episode_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    from chronocanvas.db.models.skill_invocation import SkillInvocation

    rows = await session.execute(
        select(SkillInvocation)
        .where(SkillInvocation.episode_id == episode_id)
        .order_by(SkillInvocation.created_at.desc())
    )
    out = []
    for r in rows.scalars().all():
        out.append({
            "id": str(r.id), "skill_name": r.skill_name, "model": r.model,
            "provider": r.provider, "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens, "cost_usd": r.cost_usd,
            "cost_confidence": r.cost_confidence, "status": r.status,
            "room": r.room, "gate": r.gate,
        })
    return out
