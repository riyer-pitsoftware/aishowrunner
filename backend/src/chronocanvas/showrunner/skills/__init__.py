"""Skill runtime — the Skill Plane (TRD §4, §5).

Public surface: the SkillPort contract + a settings-driven factory that builds the
configured adapter (``SHOWRUNNER_SKILL_PORT=harness|subprocess``), the registry,
and the concurrent fan-out helper.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from chronocanvas.showrunner.skills.envelope import derive_project_key
from chronocanvas.showrunner.skills.fanout import invoke_many
from chronocanvas.showrunner.skills.harness_port import HarnessSkillPort
from chronocanvas.showrunner.skills.port import (
    SkillCallRequest,
    SkillCallResult,
    SkillContribution,
    SkillPort,
    Stance,
)
from chronocanvas.showrunner.skills.registry import (
    SkillInfo,
    SkillRegistry,
    default_skills_dir,
)
from chronocanvas.showrunner.skills.subprocess_port import SubprocessSkillPort

__all__ = [
    "SkillPort", "SkillCallRequest", "SkillCallResult", "SkillContribution", "Stance",
    "SkillRegistry", "SkillInfo", "HarnessSkillPort", "SubprocessSkillPort",
    "invoke_many", "get_skill_registry", "get_skill_port",
]


def _repo_root() -> Path:
    # backend/showrunner_skills -> backend -> repo root
    return default_skills_dir().parents[1]


def _opt(value: str) -> Path | None:
    return Path(value) if value else None


@lru_cache(maxsize=1)
def get_skill_registry() -> SkillRegistry:
    from chronocanvas.config import settings

    skills_dir = _opt(settings.showrunner_skills_dir) or default_skills_dir()
    reg = SkillRegistry(skills_dir)
    reg.discover()
    return reg


def get_skill_port() -> SkillPort:
    """Build the configured SkillPort from settings (TRD §4.2)."""
    from chronocanvas.config import settings

    repo = _repo_root()
    skills_dir = _opt(settings.showrunner_skills_dir) or default_skills_dir()
    harness_repo = settings.harness_repo or str(Path.home() / "code" / "agentic-harness")
    models_path = _opt(settings.harness_models_path) or (repo / ".harness" / "models.yaml")
    planning_dir = _opt(settings.showrunner_planning_dir) or (repo / ".planning" / "build")
    project_memory_dir = _opt(settings.project_memory_dir) or (
        Path.home() / ".claude" / "projects" / derive_project_key(repo) / "memory"
    )

    if settings.skill_port == "subprocess":
        return SubprocessSkillPort(
            run_skill_path=str(Path(harness_repo) / "runtime" / "run_skill.py"),
            skills_dir=skills_dir,
            models_path=models_path,
            timeout_s=settings.skill_timeout_s,
        )
    return HarnessSkillPort(
        skills_dir=skills_dir,
        models_path=models_path,
        harness_repo=harness_repo,
        planning_dir=planning_dir,
        project_memory_dir=project_memory_dir,
        ollama_base_url=settings.ollama_base_url,
        timeout_s=settings.skill_timeout_s,
    )
