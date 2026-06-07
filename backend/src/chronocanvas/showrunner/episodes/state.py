"""Episode state machine (TRD §8.2).

DRAFT → STORY_ROOM → BRANCH_GREENLIGHT → EPISODE_PLAN → EPISODE_GREENLIGHT
      → PRODUCING → FINAL_CUT → CANON_COMMIT → DONE

Greenlight states loop back to the owning room on "reconsider"/"revise".
Transitions are explicit and validated so endpoints stay idempotent.
"""

from __future__ import annotations

from enum import Enum


class EpisodeStatus(str, Enum):
    DRAFT = "draft"
    STORY_ROOM = "story_room"
    BRANCH_GREENLIGHT = "branch_greenlight"
    EPISODE_PLAN = "episode_plan"
    EPISODE_GREENLIGHT = "episode_greenlight"
    PRODUCING = "producing"
    FINAL_CUT = "final_cut"
    CANON_COMMIT = "canon_commit"
    DONE = "done"


S = EpisodeStatus

ALLOWED_TRANSITIONS: dict[EpisodeStatus, set[EpisodeStatus]] = {
    S.DRAFT: {S.STORY_ROOM},
    S.STORY_ROOM: {S.BRANCH_GREENLIGHT},
    S.BRANCH_GREENLIGHT: {S.EPISODE_PLAN, S.STORY_ROOM},  # approve | reconsider
    S.EPISODE_PLAN: {S.EPISODE_GREENLIGHT},
    S.EPISODE_GREENLIGHT: {S.PRODUCING, S.EPISODE_PLAN},  # approve | revise
    S.PRODUCING: {S.FINAL_CUT},
    S.FINAL_CUT: {S.CANON_COMMIT, S.PRODUCING},  # approve | regenerate
    S.CANON_COMMIT: {S.DONE},
    S.DONE: set(),
}

# Which greenlight gate is pending in a given state.
_GATE_AT = {
    S.BRANCH_GREENLIGHT: "branch",
    S.EPISODE_GREENLIGHT: "episode",
    S.FINAL_CUT: "final",
}


class InvalidTransitionError(ValueError):
    pass


def _coerce(s) -> EpisodeStatus:
    return s if isinstance(s, EpisodeStatus) else EpisodeStatus(s)


def can_transition(current, target) -> bool:
    return _coerce(target) in ALLOWED_TRANSITIONS.get(_coerce(current), set())


def assert_transition(current, target) -> EpisodeStatus:
    cur, tgt = _coerce(current), _coerce(target)
    if tgt not in ALLOWED_TRANSITIONS.get(cur, set()):
        allowed = sorted(s.value for s in ALLOWED_TRANSITIONS.get(cur, set()))
        raise InvalidTransitionError(
            f"cannot move episode {cur.value} → {tgt.value}; allowed: {allowed}"
        )
    return tgt


def next_required_gate(current) -> str | None:
    """The approval gate blocking advancement from this state, if any."""
    return _GATE_AT.get(_coerce(current))
