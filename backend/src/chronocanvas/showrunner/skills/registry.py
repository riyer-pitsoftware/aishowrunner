"""Skill registry — fork-first discovery of project-owned skill forks.

Forks live in ``backend/showrunner_skills/<name>/SKILL.md`` (TRD §5.1, kept
verbatim — see memory/skill-fork-isolation). The file on disk is always the
source of truth; this registry is a cache that records a content hash so every
invocation can be attributed to an exact skill version (TRD §5.4).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml


def default_skills_dir() -> Path:
    """``backend/showrunner_skills`` relative to this file."""
    # registry.py -> skills -> showrunner -> chronocanvas -> src -> backend
    return Path(__file__).resolve().parents[4] / "showrunner_skills"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from body. Tolerant: returns ({}, text) if absent."""
    if not text.startswith("---\n"):
        return {}, text.lstrip("\n")
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    front = yaml.safe_load(text[4:end]) or {}
    body = text[end + 5 :].lstrip("\n")
    return front, body


@dataclass
class SkillInfo:
    name: str
    path: Path
    content_hash: str
    description: str
    default_tier: str | None
    role_title: str | None


def _role_title(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


class SkillRegistry:
    def __init__(self, skills_dir: Path | None = None) -> None:
        self.skills_dir = Path(skills_dir) if skills_dir else default_skills_dir()
        self._cache: dict[str, SkillInfo] = {}

    def discover(self) -> dict[str, SkillInfo]:
        """(Re)scan the skills dir. Disk always wins."""
        cache: dict[str, SkillInfo] = {}
        if self.skills_dir.is_dir():
            for child in sorted(self.skills_dir.iterdir()):
                skill_md = child / "SKILL.md"
                if not skill_md.is_file():
                    continue
                raw = skill_md.read_bytes()
                front, body = parse_frontmatter(raw.decode("utf-8", "replace"))
                meta = front.get("metadata") or {}
                tier = front.get("model_tier") or meta.get("model_tier")
                cache[child.name] = SkillInfo(
                    name=child.name,
                    path=skill_md,
                    content_hash=hashlib.sha256(raw).hexdigest(),
                    description=str(front.get("description", "")).strip(),
                    default_tier=tier,
                    role_title=_role_title(body),
                )
        self._cache = cache
        return cache

    def list(self) -> list[SkillInfo]:
        if not self._cache:
            self.discover()
        return list(self._cache.values())

    def get(self, name: str) -> SkillInfo:
        if not self._cache:
            self.discover()
        if name not in self._cache:
            # one more rescan in case a fork was just added
            self.discover()
        if name not in self._cache:
            raise KeyError(
                f"skill '{name}' not found under {self.skills_dir}. "
                f"Available: {sorted(self._cache)}"
            )
        return self._cache[name]

    def read(self, name: str) -> tuple[dict, str]:
        """Return (frontmatter, body) for a fork, read fresh from disk."""
        info = self.get(name)
        return parse_frontmatter(info.path.read_text())
