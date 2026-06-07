"""SubprocessSkillPort — process-isolated adapter via run_skill.py (TRD §4.2).

Shells out to the canonical agentic-harness CLI
(``runtime/run_skill.py``), which is self-contained (PEP-723 inline deps run via
``uv``). Strongest "invoked through agentic-harness" evidence and full process
isolation.

Limitation: ``run_skill.py`` discovers skills by name from ``~/.claude/skills``
etc. — it does NOT read our ``backend/showrunner_skills/`` forks. Use this port
for the substrate proof / isolation when canonical resolution is acceptable; use
``HarnessSkillPort`` when the project fork must be authoritative. The resolved
model is still passed via ``--model`` so routing matches ``.harness/models.yaml``.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

import yaml

from chronocanvas.showrunner.skills.envelope import parse_contribution, wrap_task
from chronocanvas.showrunner.skills.harness_port import estimate_tokens
from chronocanvas.showrunner.skills.port import SkillCallRequest, SkillCallResult
from chronocanvas.showrunner.skills.registry import SkillRegistry


class SubprocessSkillPort:
    def __init__(
        self,
        *,
        run_skill_path: str,
        skills_dir: Path | None = None,
        models_path: Path | None = None,
        timeout_s: float = 120.0,
    ) -> None:
        self.run_skill_path = run_skill_path
        self.registry = SkillRegistry(skills_dir)
        self.models_path = Path(models_path) if models_path else None
        self.timeout_s = timeout_s

    def _resolve_tier_model(self, req: SkillCallRequest) -> str | None:
        if req.model:
            return req.model
        if req.model_tier and self.models_path and self.models_path.is_file():
            cfg = yaml.safe_load(self.models_path.read_text()) or {}
            return cfg.get(req.model_tier)
        return None

    async def invoke(self, req: SkillCallRequest) -> SkillCallResult:
        try:
            info = self.registry.get(req.skill_name)
            content_hash = info.content_hash
        except KeyError:
            content_hash = ""

        argv = [self.run_skill_path, req.skill_name]
        model = self._resolve_tier_model(req)
        if model:
            argv += ["--model", model]
        user_msg = wrap_task(req.message, req.structured)

        start = time.monotonic()
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, err = await asyncio.wait_for(
                proc.communicate(user_msg.encode()), timeout=self.timeout_s
            )
        except (TimeoutError, asyncio.TimeoutError):
            return SkillCallResult(
                skill_name=req.skill_name, content="", model=model or "", provider="",
                duration_ms=(time.monotonic() - start) * 1000, status="failed",
                error="subprocess timeout", content_hash=content_hash,
            )
        except Exception as e:
            return SkillCallResult(
                skill_name=req.skill_name, content="", model=model or "", provider="",
                status="failed", error=str(e), content_hash=content_hash,
            )
        duration_ms = (time.monotonic() - start) * 1000

        if proc.returncode != 0:
            return SkillCallResult(
                skill_name=req.skill_name, content="", model=model or "", provider="",
                duration_ms=duration_ms, status="failed",
                error=(err.decode("utf-8", "replace").strip() or f"exit {proc.returncode}"),
                content_hash=content_hash,
            )

        content = out.decode("utf-8", "replace").strip()
        provider = model.split("/", 1)[0] if model and "/" in model else ""
        contribution = parse_contribution(content) if req.structured else None
        return SkillCallResult(
            skill_name=req.skill_name,
            content=content,
            model=model or "",
            provider=provider,
            input_tokens=estimate_tokens(user_msg),
            output_tokens=estimate_tokens(content),
            tokens_estimated=True,  # run_skill does not emit usage on stdout
            duration_ms=duration_ms,
            status="ok",
            content_hash=content_hash,
            contribution=contribution,
        )
