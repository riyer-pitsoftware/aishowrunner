"""Pricing — turn token usage / media units into USD (TRD §6.1, §6.2).

Pure functions over a pricing dict (loaded from config/pricing.yaml). Local
Ollama prices to $0; cloud values are placeholders until asr-av5.2. When a skill
result's tokens were estimated, the derived cost is marked ``estimated``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


def default_pricing_path() -> Path:
    # pricing.py -> cost -> showrunner -> chronocanvas -> src -> backend -> repo
    return Path(__file__).resolve().parents[5] / "config" / "pricing.yaml"


@lru_cache(maxsize=4)
def load_pricing(path: str | None = None) -> dict[str, Any]:
    p = Path(path) if path else default_pricing_path()
    if not p.is_file():
        return {}
    return yaml.safe_load(p.read_text()) or {}


def split_model(model: str) -> tuple[str, str]:
    """'qwen-cloud/qwen-plus' -> ('qwen-cloud', 'qwen-plus'); 'ollama/x' -> ('ollama','x')."""
    if "/" in model:
        provider, model_id = model.split("/", 1)
        return provider, model_id
    return model, ""


def _text_rates(provider: str, model_id: str, pricing: dict) -> tuple[float, float]:
    text = (pricing or {}).get("text", {})
    entry = text.get(provider)
    if entry is None:
        return 0.0, 0.0
    # ollama-style flat {input_per_1m, output_per_1m}
    if "input_per_1m" in entry:
        return float(entry.get("input_per_1m", 0.0)), float(entry.get("output_per_1m", 0.0))
    # nested per-model (qwen-cloud)
    model_entry = entry.get(model_id) or entry.get("default") or {}
    return float(model_entry.get("input_per_1m", 0.0)), float(model_entry.get("output_per_1m", 0.0))


def text_cost(model: str, input_tokens: int, output_tokens: int, pricing: dict) -> float:
    """USD for a text/skill call. Unknown providers/models price to 0.0."""
    provider, model_id = split_model(model or "")
    in_rate, out_rate = _text_rates(provider, model_id, pricing)
    return (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate


def media_cost(kind: str, units: float, pricing: dict) -> tuple[float, float]:
    """Return (unit_price, total_cost) for ``units`` (images / seconds / 1k-chars)."""
    entry = (pricing or {}).get("media", {}).get(kind, {})
    price = float(entry.get("price", 0.0))
    if entry.get("unit") == "per_1k_chars":
        total = (units / 1000.0) * price
    else:
        total = units * price
    return price, total


def price_skill_result(model: str, input_tokens: int, output_tokens: int,
                       tokens_estimated: bool, pricing: dict | None = None) -> tuple[float, str]:
    """Return (cost_usd, cost_confidence) for a skill invocation."""
    pricing = pricing if pricing is not None else load_pricing()
    cost = text_cost(model, input_tokens, output_tokens, pricing)
    confidence = "estimated" if tokens_estimated else "exact"
    return round(cost, 8), confidence
