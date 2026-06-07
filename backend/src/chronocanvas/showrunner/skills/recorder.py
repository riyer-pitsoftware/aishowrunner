"""Persist a SkillCallResult to the skill_invocation ledger (TRD §5.4)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.db.models.skill_invocation import SkillInvocation
from chronocanvas.showrunner.skills.port import SkillCallRequest, SkillCallResult


def _as_uuid(value) -> uuid.UUID | None:
    if value is None or isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def build_invocation(req: SkillCallRequest, result: SkillCallResult) -> SkillInvocation:
    contribution = result.contribution
    return SkillInvocation(
        series_id=_as_uuid(req.series_id),
        episode_id=_as_uuid(req.episode_id),
        decision_id=req.decision_id,
        room=req.room,
        gate=req.gate,
        skill_name=result.skill_name,
        content_hash=result.content_hash,
        model=result.model,
        provider=result.provider,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cached_tokens=result.cached_tokens,
        tokens_estimated=result.tokens_estimated,
        duration_ms=result.duration_ms,
        cost_usd=0.0,  # populated by Cost & Budgeting subsystem (asr-3mk.*)
        cost_confidence="estimated" if result.tokens_estimated else "exact",
        status=result.status,
        error=result.error,
        stance=(contribution.stance.value if contribution else None),
        summary=(contribution.summary if contribution else None),
        raw_output=result.content or None,
    )


async def record_invocation(
    session: AsyncSession, req: SkillCallRequest, result: SkillCallResult
) -> SkillInvocation:
    row = build_invocation(req, result)
    session.add(row)
    await session.flush()
    return row
