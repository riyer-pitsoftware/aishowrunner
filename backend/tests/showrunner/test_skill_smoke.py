"""Real end-to-end smoke (asr-0bj.8): a skill executes through agentic-harness on
Qwen/Ollama. Uses SubprocessSkillPort → run_skill.py (self-contained via uv), so
it needs no extra installed deps — only a reachable Ollama. Skips otherwise."""

from __future__ import annotations

import os
import urllib.request
from pathlib import Path

import pytest

from chronocanvas.showrunner.skills.port import SkillCallRequest
from chronocanvas.showrunner.skills.registry import default_skills_dir
from chronocanvas.showrunner.skills.subprocess_port import SubprocessSkillPort

REPO = default_skills_dir().parents[1]
MODELS_YAML = REPO / ".harness" / "models.yaml"
RUN_SKILL = Path.home() / "code" / "agentic-harness" / "runtime" / "run_skill.py"
OLLAMA = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


def _ollama_up() -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


@pytest.mark.skipif(not RUN_SKILL.is_file(), reason="run_skill.py not found")
@pytest.mark.skipif(not _ollama_up(), reason="Ollama not reachable")
@pytest.mark.asyncio
async def test_pessimism_runs_through_qwen_on_ollama():
    port = SubprocessSkillPort(
        run_skill_path=str(RUN_SKILL), models_path=MODELS_YAML, timeout_s=180.0
    )
    res = await port.invoke(
        SkillCallRequest(
            skill_name="pessimism",
            message="We finished the whole app and every test passes.",
            model_tier="critic",
            structured=False,
        )
    )
    assert res.status == "ok", res.error
    assert res.content.strip()
    assert res.model and "qwen" in res.model
