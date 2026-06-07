"""Bounded concurrent skill fan-out for room orchestration (TRD §4.4).

A room invokes its roster's skills *independently* and in parallel. Concurrency
is bounded to keep local Ollama / Qwen Cloud RPM in check; each call has a
timeout and one retry on dispatch failure. A persistently failing skill yields a
``status='failed'`` result rather than aborting the whole fan-out.
"""

from __future__ import annotations

import asyncio

from chronocanvas.showrunner.skills.port import (
    SkillCallRequest,
    SkillCallResult,
    SkillPort,
)


async def _invoke_one(
    port: SkillPort,
    req: SkillCallRequest,
    sem: asyncio.Semaphore,
    timeout_s: float,
    retries: int,
) -> SkillCallResult:
    last_err = "unknown error"
    async with sem:
        for attempt in range(retries + 1):
            try:
                result = await asyncio.wait_for(port.invoke(req), timeout=timeout_s)
            except (TimeoutError, asyncio.TimeoutError):
                last_err = f"timeout after {timeout_s}s"
            except Exception as e:  # defensive: a port should not raise
                last_err = str(e)
            else:
                if result.status == "ok":
                    return result
                last_err = result.error or "skill returned status=failed"
            if attempt < retries:
                await asyncio.sleep(0.5 * (2**attempt))
    return SkillCallResult(
        skill_name=req.skill_name, content="", model="", provider="",
        status="failed", error=last_err,
    )


async def invoke_many(
    port: SkillPort,
    requests: list[SkillCallRequest],
    *,
    max_concurrent: int = 3,
    timeout_s: float = 120.0,
    retries: int = 1,
) -> list[SkillCallResult]:
    """Run requests concurrently (bounded), preserving input order."""
    sem = asyncio.Semaphore(max_concurrent)
    tasks = [_invoke_one(port, r, sem, timeout_s, retries) for r in requests]
    return await asyncio.gather(*tasks)
