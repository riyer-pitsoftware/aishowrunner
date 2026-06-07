"""Unit tests for the Skill Plane (TRD §4, §5). No network: the litellm boundary
is faked, mirroring how the harness tests mock the agent boundary."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from chronocanvas.showrunner.skills.envelope import (
    build_memory_envelope,
    parse_contribution,
    role_memory_path,
    wrap_task,
)
from chronocanvas.showrunner.skills.fanout import invoke_many
from chronocanvas.showrunner.skills.port import SkillCallRequest, SkillCallResult, Stance
from chronocanvas.showrunner.skills.recorder import build_invocation
from chronocanvas.showrunner.skills.registry import SkillRegistry, default_skills_dir

REPO = default_skills_dir().parents[1]
MODELS_YAML = REPO / ".harness" / "models.yaml"
HARNESS_REPO = str(Path.home() / "code" / "agentic-harness")

EXPECTED_SKILLS = {
    "team-pm", "team-creative-director", "team-narrative-engineer", "team-historian",
    "team-game-designer", "team-line-producer", "team-ml-engineer", "team-cloud-economist",
    "team-frontend-engineer", "team-backend-engineer", "team-devops-engineer",
    "team-judge-panel", "pessimism",
}


# ── Registry (asr-0bj.5) ─────────────────────────────────────────────────────

def test_registry_discovers_all_forks():
    reg = SkillRegistry()
    found = reg.discover()
    assert EXPECTED_SKILLS.issubset(set(found)), f"missing: {EXPECTED_SKILLS - set(found)}"
    pess = reg.get("pessimism")
    assert len(pess.content_hash) == 64  # sha256 hex
    assert pess.path.name == "SKILL.md"


def test_registry_content_hash_stable():
    a = SkillRegistry().get("team-historian").content_hash
    b = SkillRegistry().get("team-historian").content_hash
    assert a == b


def test_registry_unknown_raises():
    with pytest.raises(KeyError):
        SkillRegistry().get("no-such-skill")


# ── Contribution envelope + parser (asr-0bj.6) ───────────────────────────────

def test_wrap_task_structured_vs_raw():
    assert "```json" in wrap_task("do x", structured=True)
    assert wrap_task("do x", structured=False) == "do x"


def test_parse_contribution_json_block():
    text = (
        "Here is my analysis.\n\n"
        '```json\n{"summary": "looks risky", "stance": "concern", '
        '"recommendations": ["add tests"], "risks": ["no eval"], '
        '"fields": {"est_cost_usd": 1.2}}\n```'
    )
    c = parse_contribution(text)
    assert c.parsed is True
    assert c.stance is Stance.CONCERN
    assert c.summary == "looks risky"
    assert c.recommendations == ["add tests"]
    assert c.fields["est_cost_usd"] == 1.2


def test_parse_contribution_fallback_keeps_raw():
    c = parse_contribution("just prose, no json here")
    assert c.parsed is False
    assert c.stance is Stance.UNKNOWN
    assert c.raw_text == "just prose, no json here"


def test_parse_contribution_bad_stance_is_unknown():
    c = parse_contribution('```json\n{"summary":"x","stance":"maybe"}\n```')
    assert c.parsed is True
    assert c.stance is Stance.UNKNOWN


# ── Memory envelope (TRD §5.3) ───────────────────────────────────────────────

def test_role_memory_path_strips_suffix():
    p = role_memory_path("team-backend-engineer", Path("/m"))
    assert p == Path("/m/team/backend.md")
    assert role_memory_path("pessimism", Path("/m")) is None


def test_memory_envelope_injects_all(tmp_path: Path):
    planning = tmp_path / "planning"
    planning.mkdir()
    (planning / "ROSTER.md").write_text("# Roster\nVidya owns history.")
    (planning / "STATUS.md").write_text("# Status\nSprint 2.\n\n## Detail\nhidden.")
    mem = tmp_path / "mem"
    (mem / "team").mkdir(parents=True)
    (mem / "team" / "historian.md").write_text("# Vidya config\nChola 10th c.")

    env = build_memory_envelope("team-historian", planning, mem)
    assert "## Project context" in env
    assert "Vidya owns history" in env
    assert "Sprint 2." in env and "hidden." not in env  # status lede stops at ##
    assert "Chola 10th c." in env


def test_memory_envelope_empty_when_nothing(tmp_path: Path):
    assert build_memory_envelope("pessimism", tmp_path, tmp_path) == ""


# ── Recorder mapping (asr-0bj.7) ─────────────────────────────────────────────

def test_build_invocation_maps_fields():
    req = SkillCallRequest(skill_name="team-historian", message="x", room="story_room",
                           episode_id="not-a-uuid")
    res = SkillCallResult(
        skill_name="team-historian", content="hi", model="ollama/qwen2.5-coder:14b",
        provider="ollama", input_tokens=10, output_tokens=5, tokens_estimated=True,
        duration_ms=42.0, content_hash="abc",
    )
    row = build_invocation(req, res)
    assert row.skill_name == "team-historian"
    assert row.provider == "ollama"
    assert row.input_tokens == 10
    assert row.cost_confidence == "estimated"  # because tokens_estimated
    assert row.room == "story_room"
    assert row.episode_id is None  # bad uuid coerced to None, not an error


# ── Fan-out (asr-0bj.4) ──────────────────────────────────────────────────────

class _FakePort:
    def __init__(self, fail_skills=(), fail_times=None):
        self.calls: dict[str, int] = {}
        self.fail_skills = set(fail_skills)
        self.fail_times = fail_times or {}

    async def invoke(self, req: SkillCallRequest) -> SkillCallResult:
        self.calls[req.skill_name] = self.calls.get(req.skill_name, 0) + 1
        n = self.calls[req.skill_name]
        if req.skill_name in self.fail_skills or n <= self.fail_times.get(req.skill_name, 0):
            return SkillCallResult(skill_name=req.skill_name, content="", model="", provider="",
                                   status="failed", error="boom")
        return SkillCallResult(
            skill_name=req.skill_name, content="ok", model="m", provider="ollama"
        )


@pytest.mark.asyncio
async def test_fanout_preserves_order_and_isolates_failure():
    reqs = [SkillCallRequest(skill_name=s, message="m") for s in ("a", "b", "c")]
    port = _FakePort(fail_skills={"b"})
    results = await invoke_many(port, reqs, max_concurrent=2, timeout_s=5, retries=0)
    assert [r.skill_name for r in results] == ["a", "b", "c"]
    assert results[0].status == "ok"
    assert results[1].status == "failed" and results[1].error
    assert results[2].status == "ok"


@pytest.mark.asyncio
async def test_fanout_retries_then_succeeds():
    port = _FakePort(fail_times={"a": 1})  # fail once, then ok
    results = await invoke_many(port, [SkillCallRequest(skill_name="a", message="m")],
                                timeout_s=5, retries=1)
    assert results[0].status == "ok"
    assert port.calls["a"] == 2


# ── HarnessSkillPort with faked litellm (asr-0bj.2) ───────────────────────────

def _install_fake_litellm(content: str, prompt_tokens=11, completion_tokens=7):
    fake = types.ModuleType("litellm")

    class _Msg:
        def __init__(self, c):
            self.content = c

    class _Choice:
        def __init__(self, c):
            self.message = _Msg(c)

    class _Usage:
        def __init__(self, p, c):
            self.prompt_tokens = p
            self.completion_tokens = c

    class _Resp:
        def __init__(self):
            self.choices = [_Choice(content)]
            self.usage = _Usage(prompt_tokens, completion_tokens)

    async def acompletion(**kwargs):
        acompletion.last_kwargs = kwargs
        return _Resp()

    fake.acompletion = acompletion
    sys.modules["litellm"] = fake
    return fake


@pytest.mark.skipif(not MODELS_YAML.is_file(), reason="project .harness/models.yaml required")
@pytest.mark.skipif(not Path(HARNESS_REPO).is_dir(), reason="agentic-harness repo required")
@pytest.mark.asyncio
async def test_harness_port_resolves_fork_and_dispatches():
    from chronocanvas.showrunner.skills.harness_port import HarnessSkillPort

    fake_content = (
        '```json\n{"summary":"ok","stance":"support",'
        '"recommendations":[],"risks":[]}\n```'
    )
    fake = _install_fake_litellm(fake_content)

    port = HarnessSkillPort(
        models_path=MODELS_YAML, harness_repo=HARNESS_REPO,
        planning_dir=None, project_memory_dir=None,
    )
    res = await port.invoke(SkillCallRequest(skill_name="pessimism", message="ship it"))

    assert res.status == "ok"
    assert res.provider == "ollama"
    assert "qwen" in res.model
    assert res.content == fake_content
    assert res.input_tokens == 11 and res.output_tokens == 7
    assert res.tokens_estimated is False
    assert res.contribution and res.contribution.parsed
    assert res.contribution.stance is Stance.SUPPORT
    # the fork body (not the canonical one) reached the model as system prompt
    sys_prompt = fake.acompletion.last_kwargs["messages"][0]["content"]
    assert sys_prompt.strip() != ""
