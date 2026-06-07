"""Real-time event types + payloads (TRD §12).

Pure ``event_payload`` builders (testable) plus a thin async ``RoomPublisher``
over the existing Redis ``ProgressPublisher``. Channels are keyed by episode id.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class EventType(str, Enum):
    ROOM_STARTED = "room_started"
    SKILL_CONTRIBUTION_READY = "skill_contribution_ready"
    DISAGREEMENT_DETECTED = "disagreement_detected"
    GATE_PENDING = "gate_pending"
    GATE_DECIDED = "gate_decided"
    PRODUCTION_STAGE = "production_stage"
    ARTIFACT_READY = "artifact_ready"
    BUDGET_WARNING = "budget_warning"
    BUDGET_EXCEEDED = "budget_exceeded"
    TERMINAL = "terminal"


def channel_for(episode_id: str) -> str:
    return f"episode:{episode_id}"


def event_payload(event: EventType, **data: Any) -> dict[str, Any]:
    return {"type": event.value, **data}


class RoomPublisher:
    """Async wrapper over services.progress.ProgressPublisher (Redis pub/sub)."""

    def __init__(self, episode_id: str, publisher: Any | None = None) -> None:
        self.episode_id = episode_id
        self.channel = channel_for(episode_id)
        self._publisher = publisher  # injectable for tests

    async def emit(self, event: EventType, **data: Any) -> None:
        payload = event_payload(event, episode_id=self.episode_id, **data)
        pub = self._publisher
        if pub is None:
            from chronocanvas.services.progress import ProgressPublisher

            pub = ProgressPublisher()
        await pub.publish(self.channel, payload)
