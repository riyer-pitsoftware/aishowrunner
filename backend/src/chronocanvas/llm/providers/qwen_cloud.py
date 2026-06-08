"""Qwen Cloud provider — Alibaba DashScope, OpenAI-compatible (asr-av5.1).

Wires the ChronoCanvas media-plane LLM (`chronocanvas.llm`) to real Qwen Cloud,
so the continuity eval (`settings.eval_model = "qwen-cloud/qwen-plus"`) and any
`provider="qwen-cloud"` routing resolve to DashScope instead of local Ollama.

DashScope exposes an OpenAI-compatible REST surface at
``/compatible-mode/v1/chat/completions``; we call it over ``httpx`` (a hard
dependency, unlike the optional ``openai`` SDK) to match the Ollama / DashScope
media providers and keep pure/offline test collection dependency-free.

Cost is priced from the shared ``config/pricing.yaml`` (TRD §6.2) so this stays
the single source of truth — every invocation records ``provider="qwen-cloud"``.
"""

from __future__ import annotations

import httpx

from chronocanvas.config import settings
from chronocanvas.llm.base import LLMProvider, LLMResponse


def _api_key() -> str:
    """Explicit Qwen Cloud key, falling back to the DashScope key (same vendor)."""
    return settings.qwen_cloud_api_key or settings.dashscope_api_key


class QwenCloudProvider(LLMProvider):
    name = "qwen-cloud"

    def __init__(self) -> None:
        self.base_url = settings.qwen_cloud_base_url.rstrip("/")
        # The model id used when callers don't override; mirrors the balanced
        # eval tier. Strip any "qwen-cloud/" prefix so the wire id is bare.
        eval_model = settings.eval_model or "qwen-cloud/qwen-plus"
        self.model = eval_model.split("/", 1)[1] if "/" in eval_model else eval_model

    def _cost(self, input_tokens: int, output_tokens: int) -> float:
        # Priced from config/pricing.yaml via the showrunner cost helpers so the
        # ledger and the router agree on a single rate table.
        from chronocanvas.showrunner.cost.pricing import load_pricing, text_cost

        return text_cost(
            f"{self.name}/{self.model}", input_tokens, output_tokens, load_pricing()
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False,
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions", json=payload, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()

        choices = data.get("choices") or [{}]
        content = (choices[0].get("message") or {}).get("content") or ""
        usage = data.get("usage") or {}
        input_tokens = int(usage.get("prompt_tokens", 0) or 0)
        output_tokens = int(usage.get("completion_tokens", 0) or 0)

        return LLMResponse(
            content=content,
            provider=self.name,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=self._cost(input_tokens, output_tokens),
        )

    async def is_available(self) -> bool:
        return bool(_api_key())
