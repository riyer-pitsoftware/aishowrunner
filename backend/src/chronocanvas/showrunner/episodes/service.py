"""Episode lifecycle service — create + idempotent transitions (TRD §8.2)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.showrunner.episodes.state import (
    EpisodeStatus,
    assert_transition,
    next_required_gate,
)


class EpisodeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_episode(self, series_id: uuid.UUID, *, title=None, premise=None):
        from chronocanvas.db.models.showrunner_episode import Episode

        nxt = await self.session.execute(
            select(func.coalesce(func.max(Episode.number), 0)).where(
                Episode.series_id == series_id
            )
        )
        number = int(nxt.scalar() or 0) + 1
        ep = Episode(
            series_id=series_id, number=number, title=title, premise=premise,
            status=EpisodeStatus.DRAFT.value,
        )
        self.session.add(ep)
        await self.session.flush()
        return ep

    async def get(self, episode_id: uuid.UUID):
        from chronocanvas.db.models.showrunner_episode import Episode

        return await self.session.get(Episode, episode_id)

    async def advance(self, episode, target: EpisodeStatus | str):
        cur = EpisodeStatus(episode.status)
        tgt = target if isinstance(target, EpisodeStatus) else EpisodeStatus(target)
        if cur != tgt:
            assert_transition(cur, tgt)  # raises InvalidTransitionError
            episode.status = tgt.value
            await self.session.flush()
        return episode

    @staticmethod
    def describe(episode) -> dict:
        return {
            "id": str(episode.id),
            "series_id": str(episode.series_id),
            "number": episode.number,
            "title": episode.title,
            "status": episode.status,
            "active_room": episode.active_room,
            "next_required_gate": next_required_gate(episode.status),
        }
