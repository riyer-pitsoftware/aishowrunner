"""Greenlight gates (TRD §8.2/§8.3) — record a decision, snapshot dissent, and
advance the episode state machine idempotently. Budget is reserved at the
episode gate (TRD §6.6).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.showrunner.episodes.state import (
    EpisodeStatus,
    assert_transition,
)
from chronocanvas.showrunner.rooms.events import EventType, RoomPublisher

S = EpisodeStatus

# gate -> (greenlight state, approved-forward state)
GATE_FORWARD: dict[str, tuple[EpisodeStatus, EpisodeStatus]] = {
    "branch": (S.BRANCH_GREENLIGHT, S.EPISODE_PLAN),
    "episode": (S.EPISODE_GREENLIGHT, S.PRODUCING),
    "final": (S.FINAL_CUT, S.CANON_COMMIT),
}
# gate -> loop-back state on reconsider/revise/reduce/defer
GATE_LOOPBACK: dict[str, EpisodeStatus] = {
    "branch": S.STORY_ROOM,
    "episode": S.EPISODE_PLAN,
    "final": S.PRODUCING,
}
_FORWARD_VERDICTS = {"approved", "ship", "approve"}
_LOOPBACK_VERDICTS = {"defer", "reduce", "revise", "reconsider"}


def gate_target(gate: str, verdict: str) -> EpisodeStatus | None:
    """Target state for a gate decision (pure). None = no transition (e.g. kill)."""
    v = (verdict or "").lower().strip()
    if gate not in GATE_FORWARD:
        raise ValueError(f"unknown gate '{gate}'; expected branch|episode|final")
    if v in _FORWARD_VERDICTS:
        return GATE_FORWARD[gate][1]
    if v in _LOOPBACK_VERDICTS:
        return GATE_LOOPBACK[gate]
    return None  # kill / unknown -> stay


def idempotent_transition(current: EpisodeStatus, target: EpisodeStatus) -> EpisodeStatus:
    """Return target; no-op if already there; else validate the transition (pure)."""
    cur = current if isinstance(current, EpisodeStatus) else EpisodeStatus(current)
    tgt = target if isinstance(target, EpisodeStatus) else EpisodeStatus(target)
    if cur == tgt:
        return tgt
    return assert_transition(cur, tgt)


class GateService:
    def __init__(self, session: AsyncSession, *, publisher=None) -> None:
        self.session = session
        self.publisher = publisher

    async def _dissent_snapshot(self, episode_id: uuid.UUID, decision_id: str | None) -> dict:
        from chronocanvas.db.models.showrunner_room import SpecialistDisagreement

        q = select(SpecialistDisagreement).where(
            SpecialistDisagreement.episode_id == episode_id
        )
        if decision_id:
            q = q.where(SpecialistDisagreement.decision_id == decision_id)
        rows = (await self.session.execute(q)).scalars().all()
        return {
            "disagreements": [
                {"axis": r.axis, "stances": r.stances, "detail": r.detail} for r in rows
            ]
        }

    async def record_gate(
        self,
        episode,
        *,
        gate: str,
        verdict: str,
        actor: str | None = None,
        chosen_option_id: uuid.UUID | None = None,
        rationale: str | None = None,
        decision_id: str | None = None,
    ):
        """Record an immutable ApprovalGate (with frozen dissent) and advance state."""
        from chronocanvas.db.models.showrunner_room import ApprovalGate

        snapshot = await self._dissent_snapshot(episode.id, decision_id)
        gate_row = ApprovalGate(
            episode_id=episode.id, gate=gate, verdict=verdict, actor=actor,
            decision_id=decision_id, chosen_option_id=chosen_option_id,
            dissent_snapshot=snapshot, rationale=rationale,
        )
        self.session.add(gate_row)

        target = gate_target(gate, verdict)
        if target is not None:
            new_status = idempotent_transition(EpisodeStatus(episode.status), target)
            episode.status = new_status.value
        await self.session.flush()

        pub = RoomPublisher(str(episode.id), self.publisher)
        await pub.emit(
            EventType.GATE_DECIDED, gate=gate, verdict=verdict,
            status=episode.status, dissent_count=len(snapshot["disagreements"]),
        )
        return gate_row
