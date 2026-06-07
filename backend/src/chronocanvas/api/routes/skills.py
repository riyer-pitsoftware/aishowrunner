"""Skill registry API — expose the project-owned skill forks (PRD §8, TRD §5.1).

Skill role text is never duplicated into source; these endpoints read the forks
on disk so updating a fork changes what the product reports.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from chronocanvas.showrunner.skills import get_skill_registry
from chronocanvas.showrunner.skills.registry import SkillInfo, parse_frontmatter

router = APIRouter(prefix="/skills", tags=["skills"])


def _summary(info: SkillInfo) -> dict:
    return {
        "name": info.name,
        "description": info.description,
        "role_title": info.role_title,
        "default_tier": info.default_tier,
        "content_hash": info.content_hash,
        "source_path": str(info.path),
    }


@router.get("")
def list_skills() -> list[dict]:
    registry = get_skill_registry()
    registry.discover()  # disk always wins
    return [_summary(i) for i in registry.list()]


@router.get("/{skill_name}")
def get_skill(skill_name: str) -> dict:
    registry = get_skill_registry()
    try:
        info = registry.get(skill_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"skill '{skill_name}' not found")
    front, body = parse_frontmatter(info.path.read_text())
    return {**_summary(info), "frontmatter": front, "body": body}
