"""Cost rollup — skills + media spend for an episode (TRD §6.3)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def episode_cost_rollup(session: AsyncSession, episode_id: uuid.UUID) -> dict:
    from chronocanvas.db.models.showrunner_cost import MediaGeneration
    from chronocanvas.db.models.skill_invocation import SkillInvocation

    skill_q = await session.execute(
        select(
            func.coalesce(func.sum(SkillInvocation.cost_usd), 0.0),
            func.count(SkillInvocation.id),
        ).where(SkillInvocation.episode_id == episode_id)
    )
    skill_cost, skill_calls = skill_q.one()

    media_q = await session.execute(
        select(
            func.coalesce(func.sum(MediaGeneration.cost_usd), 0.0),
            func.count(MediaGeneration.id),
        ).where(MediaGeneration.episode_id == episode_id)
    )
    media_cost_total, media_jobs = media_q.one()

    # any estimated skill cost => the rollup is an estimate
    est_q = await session.execute(
        select(func.count(SkillInvocation.id)).where(
            SkillInvocation.episode_id == episode_id,
            SkillInvocation.cost_confidence == "estimated",
        )
    )
    estimated = (est_q.scalar() or 0) > 0

    return {
        "episode_id": str(episode_id),
        "skill_cost_usd": round(float(skill_cost), 6),
        "skill_calls": int(skill_calls),
        "media_cost_usd": round(float(media_cost_total), 6),
        "media_jobs": int(media_jobs),
        "total_usd": round(float(skill_cost) + float(media_cost_total), 6),
        "confidence": "estimated" if estimated else "exact",
    }
