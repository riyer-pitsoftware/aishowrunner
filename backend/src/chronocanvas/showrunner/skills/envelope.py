"""Memory-injection + structured-contribution envelopes.

Two concerns, both at *call time* (forks stay verbatim — TRD §5.3, memory/
skill-fork-isolation):

1. **Memory envelope** — mirror the agentic-harness SKILL-FORMAT contract:
   prepend ROSTER + STATUS lede + per-role project memory to the skill body.
2. **Contribution envelope** — wrap the room task with a JSON output contract, and
   tolerantly parse the model's reply back into a ``SkillContribution``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from chronocanvas.showrunner.skills.port import SkillContribution, Stance

# --------------------------------------------------------------------------- #
# Memory envelope (mirrors agentic-harness docs/SKILL-FORMAT.md)
# --------------------------------------------------------------------------- #

_ROLE_SUFFIXES = ("-engineer", "-architect")


def derive_project_key(project_root: Path) -> str:
    """Claude Code auto-memory convention: ``-Users-x-code-foo``."""
    resolved = Path(project_root).resolve()
    return "-" + "-".join(resolved.parts[1:])


def role_memory_path(skill_name: str, project_memory_dir: Path) -> Path | None:
    """Map a ``team-*`` skill to its role-memory file under the project memory dir."""
    if not skill_name.startswith("team-"):
        return None
    role = skill_name[len("team-") :]
    for suffix in _ROLE_SUFFIXES:
        if role.endswith(suffix):
            role = role[: -len(suffix)]
            break
    return Path(project_memory_dir) / "team" / f"{role}.md"


def _status_lede(text: str) -> str:
    lines, in_lede, out = text.splitlines(), False, []
    for line in lines:
        if line.startswith("# "):
            in_lede = True
            out.append(line)
            continue
        if in_lede and line.startswith("## "):
            break
        out.append(line)
    return "\n".join(out).strip()


def build_memory_envelope(
    skill_name: str,
    planning_dir: Path | None,
    project_memory_dir: Path | None,
) -> str:
    """Render the ## Project context block (empty string if nothing to inject)."""
    roster = status = role_memory = None
    if planning_dir:
        planning_dir = Path(planning_dir)
        rp = planning_dir / "ROSTER.md"
        sp = planning_dir / "STATUS.md"
        if rp.is_file():
            roster = rp.read_text()
        if sp.is_file():
            status = _status_lede(sp.read_text())
    if project_memory_dir:
        rmp = role_memory_path(skill_name, Path(project_memory_dir))
        if rmp and rmp.is_file():
            role_memory = rmp.read_text()

    if not any([roster, status, role_memory]):
        return ""
    sections = ["## Project context\n"]
    if roster:
        sections.append(f"### Roster\n{roster}\n")
    if status:
        sections.append(f"### Status\n{status}\n")
    if role_memory:
        sections.append(f"### Role memory\n{role_memory}\n")
    sections.append("---\n\n")
    return "\n".join(sections)


# --------------------------------------------------------------------------- #
# Contribution envelope + tolerant parser
# --------------------------------------------------------------------------- #

_CONTRIBUTION_CONTRACT = """
---
After your specialist analysis (in prose), append EXACTLY ONE fenced code block
tagged `json` matching this contract (no commentary after it):

```json
{
  "summary": "one-sentence headline of your judgment",
  "stance": "support | concern | block",
  "recommendations": ["..."],
  "risks": ["..."],
  "fields": {}
}
```
`stance`: "support" if you endorse, "concern" if you have reservations, "block"
if this must not proceed. Put role-specific structured data in `fields`.
""".strip()


def wrap_task(message: str, structured: bool = True) -> str:
    """Wrap a room task with the structured-output contract."""
    if not structured:
        return message
    return f"<task>\n{message}\n</task>\n\n{_CONTRIBUTION_CONTRACT}"


_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
_ANY_OBJECT = re.compile(r"(\{.*\})", re.DOTALL)


def _coerce_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def parse_contribution(text: str) -> SkillContribution:
    """Extract the last fenced ```json block; fall back to raw text (TRD §5.3).

    Never raises — an unparseable reply still yields a displayable contribution.
    """
    candidate = None
    blocks = _JSON_BLOCK.findall(text or "")
    if blocks:
        candidate = blocks[-1]
    else:
        m = _ANY_OBJECT.search(text or "")
        if m:
            candidate = m.group(1)

    if candidate:
        try:
            data = json.loads(candidate)
            stance_raw = str(data.get("stance", "unknown")).lower().strip()
            stance = (
                Stance(stance_raw)
                if stance_raw in Stance._value2member_map_
                else Stance.UNKNOWN
            )
            return SkillContribution(
                summary=(str(data["summary"]).strip() if data.get("summary") else None),
                stance=stance,
                recommendations=_coerce_list(data.get("recommendations")),
                risks=_coerce_list(data.get("risks")),
                fields=data.get("fields") if isinstance(data.get("fields"), dict) else {},
                raw_text=text,
                parsed=True,
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    return SkillContribution(raw_text=text or "", parsed=False)
