"""HarnessSkillPort — primary in-process skill adapter (TRD §4.2).

Loads the project fork from ``backend/showrunner_skills/`` (fork-first), resolves
the model tier via the agentic-harness Layer-B function ``resolve_model`` against
``.harness/models.yaml``, injects the memory envelope, and dispatches via
``litellm`` (async; the same dispatcher the canonical ``run_skill.py`` uses).

litellm returns token usage, which feeds the cost ledger (TRD §6.1) — this is how
we work around ``HarnessAgent.AgentResult`` not exposing tokens
(memory/harness-token-gap).
"""

from __future__ import annotations

import importlib.util
import time
from functools import lru_cache
from pathlib import Path

import yaml

from chronocanvas.showrunner.skills.envelope import (
    build_memory_envelope,
    parse_contribution,
    wrap_task,
)
from chronocanvas.showrunner.skills.port import SkillCallRequest, SkillCallResult
from chronocanvas.showrunner.skills.registry import SkillRegistry


def estimate_tokens(text: str) -> int:
    """Rough fallback when a provider omits usage (~4 chars/token)."""
    return max(1, len(text or "") // 4)


@lru_cache(maxsize=4)
def _load_resolve_model(harness_repo: str):
    """Load the harness Layer-B ``resolve_model`` (single source of truth for tier
    precedence) directly from run_skill.py by path — bypassing ``runtime/__init__``,
    which pulls pydantic_ai (not a backend dependency)."""
    path = Path(harness_repo) / "runtime" / "run_skill.py"
    spec = importlib.util.spec_from_file_location("harness_run_skill", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load run_skill.py at {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.resolve_model


class HarnessSkillPort:
    def __init__(
        self,
        *,
        skills_dir: Path | None = None,
        models_path: Path | None = None,
        harness_repo: str = "",
        planning_dir: Path | None = None,
        project_memory_dir: Path | None = None,
        ollama_base_url: str = "http://localhost:11434",
        timeout_s: float = 120.0,
    ) -> None:
        self.registry = SkillRegistry(skills_dir)
        self.models_path = Path(models_path) if models_path else None
        self.harness_repo = harness_repo
        self.planning_dir = planning_dir
        self.project_memory_dir = project_memory_dir
        self.ollama_base_url = ollama_base_url
        self.timeout_s = timeout_s

    def _models_cfg(self) -> dict:
        if self.models_path and self.models_path.is_file():
            return yaml.safe_load(self.models_path.read_text()) or {}
        return {}

    def _resolve(self, front: dict, req: SkillCallRequest) -> str:
        cfg = self._models_cfg()
        override = req.model
        if override is None and req.model_tier:
            override = cfg.get(req.model_tier)
        resolve_model = _load_resolve_model(self.harness_repo)
        return resolve_model(front, cfg, override)

    async def invoke(self, req: SkillCallRequest) -> SkillCallResult:
        info = self.registry.get(req.skill_name)
        front, body = self.registry.read(req.skill_name)
        try:
            model = self._resolve(front, req)
        except Exception as e:  # bad tier / missing models.yaml
            return SkillCallResult(
                skill_name=req.skill_name, content="", model="", provider="",
                status="failed", error=f"model resolution failed: {e}",
                content_hash=info.content_hash,
            )
        provider = model.split("/", 1)[0] if "/" in model else model

        system_prompt = build_memory_envelope(
            req.skill_name, self.planning_dir, self.project_memory_dir
        ) + body
        user_msg = wrap_task(req.message, req.structured)

        import litellm  # imported lazily so pure modules stay dependency-free

        kwargs: dict = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            "timeout": self.timeout_s,
        }
        if provider == "ollama":
            kwargs["api_base"] = self.ollama_base_url

        start = time.monotonic()
        try:
            resp = await litellm.acompletion(**kwargs)
        except Exception as e:
            return SkillCallResult(
                skill_name=req.skill_name, content="", model=model, provider=provider,
                duration_ms=(time.monotonic() - start) * 1000, status="failed",
                error=str(e), content_hash=info.content_hash,
            )
        duration_ms = (time.monotonic() - start) * 1000

        content = (resp.choices[0].message.content or "") if resp.choices else ""
        usage = getattr(resp, "usage", None)
        in_tok = getattr(usage, "prompt_tokens", 0) or 0
        out_tok = getattr(usage, "completion_tokens", 0) or 0
        estimated = False
        if not in_tok and not out_tok:
            in_tok = estimate_tokens(system_prompt + user_msg)
            out_tok = estimate_tokens(content)
            estimated = True

        contribution = parse_contribution(content) if req.structured else None
        return SkillCallResult(
            skill_name=req.skill_name,
            content=content,
            model=model,
            provider=provider,
            input_tokens=in_tok,
            output_tokens=out_tok,
            tokens_estimated=estimated,
            duration_ms=duration_ms,
            status="ok",
            content_hash=info.content_hash,
            contribution=contribution,
        )
