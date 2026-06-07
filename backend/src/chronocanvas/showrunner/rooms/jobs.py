"""Background room jobs — run a room with its own DB session + skill port.

Invoked via FastAPI BackgroundTasks (demo-scale) or an ARQ worker. The HTTP
handler returns an episode id immediately; progress streams over Redis (TRD §4.1).
"""

from __future__ import annotations

import logging
import uuid

from chronocanvas.showrunner.episodes.state import EpisodeStatus
from chronocanvas.showrunner.rooms.base import RoomService

logger = logging.getLogger(__name__)


async def run_room_job(
    series_id: uuid.UUID,
    episode_id: uuid.UUID,
    room_key: str,
    task: str,
    *,
    advance_to: str | None = None,
    decision_id: str | None = None,
) -> None:
    from chronocanvas.db.engine import async_session
    from chronocanvas.showrunner.episodes.service import EpisodeService
    from chronocanvas.showrunner.skills import get_skill_port

    port = get_skill_port()
    async with async_session() as session:
        try:
            svc = EpisodeService(session)
            episode = await svc.get(episode_id)
            if episode is not None and advance_to:
                try:
                    await svc.advance(episode, EpisodeStatus(advance_to))
                except Exception as e:  # already past / invalid — keep going
                    logger.warning("episode advance skipped: %s", e)
            await RoomService(session, port).run_room(
                room_key, series_id=series_id, episode_id=episode_id,
                task=task, decision_id=decision_id,
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("room job failed (episode=%s room=%s)", episode_id, room_key)
