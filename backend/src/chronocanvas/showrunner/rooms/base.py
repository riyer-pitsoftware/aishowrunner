"""RoomService — orchestrate one room: fan out single-skill calls, persist
contributions + invocations, detect disagreement, emit events (TRD §8.1).

DB-coupled; the pure pieces it composes (build_requests, detect_disagreements,
pricing, fold) are unit-tested independently.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.showrunner.cost.pricing import load_pricing
from chronocanvas.showrunner.rooms.briefing import build_briefing
from chronocanvas.showrunner.rooms.definitions import ROOMS, build_requests
from chronocanvas.showrunner.rooms.disagreement import detect_disagreements
from chronocanvas.showrunner.rooms.events import EventType, RoomPublisher
from chronocanvas.showrunner.skills import invoke_many
from chronocanvas.showrunner.skills.port import SkillPort
from chronocanvas.showrunner.skills.recorder import build_invocation


class RoomService:
    def __init__(
        self,
        session: AsyncSession,
        port: SkillPort,
        *,
        publisher=None,
        pricing: dict | None = None,
        max_concurrent: int = 3,
        timeout_s: float = 120.0,
    ) -> None:
        self.session = session
        self.port = port
        self.publisher = publisher
        self.pricing = pricing if pricing is not None else load_pricing()
        self.max_concurrent = max_concurrent
        self.timeout_s = timeout_s

    async def run_room(
        self,
        room_key: str,
        *,
        series_id: uuid.UUID,
        episode_id: uuid.UUID,
        task: str,
        decision_id: str | None = None,
    ) -> dict:
        from chronocanvas.db.models.showrunner_room import (
            SkillContribution,
            SpecialistDisagreement,
        )

        room = ROOMS[room_key]
        pub = RoomPublisher(str(episode_id), self.publisher)
        await pub.emit(EventType.ROOM_STARTED, room=room_key, skills=list(room.skills))

        briefing = await build_briefing(self.session, series_id)
        requests = build_requests(
            room, briefing=briefing, task=task,
            series_id=str(series_id), episode_id=str(episode_id), decision_id=decision_id,
        )
        results = await invoke_many(
            self.port, requests,
            max_concurrent=self.max_concurrent, timeout_s=self.timeout_s,
        )

        compare_rows: list[dict] = []
        for req, result in zip(requests, results):
            inv = build_invocation(req, result, self.pricing)
            inv.room = room_key
            self.session.add(inv)
            await self.session.flush()

            contrib = result.contribution
            row = SkillContribution(
                episode_id=episode_id, invocation_id=inv.id, room=room_key,
                skill_name=result.skill_name, decision_id=decision_id,
                stance=(contrib.stance.value if contrib else None),
                summary=(contrib.summary if contrib else None),
                recommendations=(contrib.recommendations if contrib else []),
                risks=(contrib.risks if contrib else []),
                fields=(contrib.fields if contrib else {}),
                raw_text=result.content,
            )
            self.session.add(row)
            compare_rows.append({
                "skill_name": result.skill_name,
                "stance": (contrib.stance.value if contrib else "unknown"),
                "fields": (contrib.fields if contrib else {}),
            })
            await pub.emit(
                EventType.SKILL_CONTRIBUTION_READY, room=room_key,
                skill=result.skill_name, stance=compare_rows[-1]["stance"],
                status=result.status,
            )

        disagreements = detect_disagreements(compare_rows, decision_id)
        for d in disagreements:
            self.session.add(SpecialistDisagreement(episode_id=episode_id, **d))
            await pub.emit(EventType.DISAGREEMENT_DETECTED, room=room_key,
                           axis=d["axis"], detail=d["detail"])

        from chronocanvas.db.models.showrunner_episode import Episode

        episode = await self.session.get(Episode, episode_id)
        if episode is not None:
            episode.active_room = room_key
        await self.session.flush()

        return {
            "room": room_key,
            "contributions": compare_rows,
            "disagreements": disagreements,
        }
