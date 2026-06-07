"""Room rosters + per-skill task construction (PRD §4, TRD §8.1).

The roster is *data* — exactly the PRD skills, no replacement personas. Each room
builds one single-skill request per member from a shared briefing + a per-skill
focus line; the orchestrator fans these out independently.
"""

from __future__ import annotations

from dataclasses import dataclass

from chronocanvas.showrunner.skills.port import SkillCallRequest


@dataclass(frozen=True)
class RoomDef:
    key: str
    title: str
    skills: tuple[str, ...]
    focus: dict[str, str]  # skill_name -> focus line


STORY_ROOM = RoomDef(
    key="story_room",
    title="Story Room",
    skills=(
        "team-creative-director",
        "team-narrative-engineer",
        "team-historian",
        "team-game-designer",
    ),
    focus={
        "team-creative-director": "Judge whether the direction serves the historical-noir identity.",
        "team-narrative-engineer": "Design the hook, beats, pacing, retention, and the cliffhanger.",
        "team-historian": "Assess historical accuracy; classify each claim as fact or fiction; flag gaps. Put your verdict in fields.accuracy.",
        "team-game-designer": "Design the closing audience choices, their consequences, and branching state.",
    },
)

PRODUCTION_DESK = RoomDef(
    key="production_desk",
    title="Production Desk",
    skills=(
        "team-line-producer",
        "team-ml-engineer",
        "team-cloud-economist",
        "team-frontend-engineer",
        "team-backend-engineer",
        "team-devops-engineer",
    ),
    focus={
        "team-line-producer": "Turn the plan into a shot list + dependency notes; flag production risk.",
        "team-ml-engineer": "Choose Qwen/Wan/CosyVoice workflows; note continuity-eval needs.",
        "team-cloud-economist": "Produce a cost envelope; put est_cost_usd and budget_risk in fields.",
        "team-frontend-engineer": "Note Episode Room interaction needs for this episode.",
        "team-backend-engineer": "Note persistence/orchestration/job needs and failure recovery.",
        "team-devops-engineer": "Note runtime/deploy/observability implications.",
    },
)

GREENLIGHT = RoomDef(
    key="greenlight",
    title="Greenlight Council",
    skills=("team-pm", "team-judge-panel", "pessimism"),
    focus={
        "team-pm": "Make a ship/defer/reduce/kill call against deadline and the judging criteria.",
        "team-judge-panel": "Score UX, technical depth, demo visibility, emotional impact.",
        "pessimism": "Challenge unsupported completion claims; demand verification.",
    },
)

ROOMS: dict[str, RoomDef] = {r.key: r for r in (STORY_ROOM, PRODUCTION_DESK, GREENLIGHT)}


def build_requests(
    room: RoomDef,
    *,
    briefing: str,
    task: str,
    series_id: str | None = None,
    episode_id: str | None = None,
    decision_id: str | None = None,
    model_tier: str | None = None,
) -> list[SkillCallRequest]:
    """One independent single-skill request per room member."""
    requests = []
    for skill in room.skills:
        focus = room.focus.get(skill, "")
        message = (
            f"{briefing}\n\n## Your task\n{task}\n\n## Your focus as {skill}\n{focus}"
        )
        requests.append(
            SkillCallRequest(
                skill_name=skill,
                message=message,
                model_tier=model_tier,
                structured=True,
                series_id=series_id,
                episode_id=episode_id,
                decision_id=decision_id,
                room=room.key,
            )
        )
    return requests
