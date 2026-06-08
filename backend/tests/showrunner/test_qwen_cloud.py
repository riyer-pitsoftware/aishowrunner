"""Qwen Cloud provider + verified pricing (asr-av5.1 / asr-av5.2).

Pure/offline tests assert the pricing.yaml placeholders are gone (nonzero text
and media costs) and that the QwenCloudProvider instantiates and reports
unavailable without a key. A guarded live smoke (skipped unless QWEN_CLOUD_LIVE=1
and a real DashScope key are set) makes one real generate() call.
"""

from __future__ import annotations

import os

import pytest

from chronocanvas.showrunner.cost.pricing import load_pricing, media_cost, text_cost


# ── asr-av5.2: verified pricing (placeholders removed) ─────────────────────────


def test_qwen_cloud_text_pricing_is_nonzero():
    pricing = load_pricing()
    cost = text_cost("qwen-cloud/qwen-plus", 1_000_000, 1_000_000, pricing)
    # qwen-plus intl: $0.40 in + $1.20 out per 1M = $1.60 for 1M+1M.
    assert cost > 0.0
    assert cost == pytest.approx(1.60, rel=1e-6)


@pytest.mark.parametrize("model", ["qwen-turbo", "qwen-plus", "qwen-max"])
def test_qwen_cloud_all_tiers_priced(model):
    pricing = load_pricing()
    assert text_cost(f"qwen-cloud/{model}", 1_000_000, 0, pricing) > 0.0
    assert text_cost(f"qwen-cloud/{model}", 0, 1_000_000, pricing) > 0.0


@pytest.mark.parametrize("kind", ["image", "video", "tts"])
def test_media_pricing_is_nonzero(kind):
    pricing = load_pricing()
    unit_price, total = media_cost(kind, 1, pricing)
    assert unit_price > 0.0
    assert total > 0.0


# ── asr-av5.1: provider class ──────────────────────────────────────────────────


def test_provider_instantiates_and_unavailable_without_key(monkeypatch):
    from chronocanvas.config import settings
    from chronocanvas.llm.providers.qwen_cloud import QwenCloudProvider

    monkeypatch.setattr(settings, "qwen_cloud_api_key", "", raising=False)
    monkeypatch.setattr(settings, "dashscope_api_key", "", raising=False)

    provider = QwenCloudProvider()
    assert provider.name == "qwen-cloud"

    import asyncio

    assert asyncio.run(provider.is_available()) is False


def test_provider_available_with_key(monkeypatch):
    from chronocanvas.config import settings
    from chronocanvas.llm.providers.qwen_cloud import QwenCloudProvider

    monkeypatch.setattr(settings, "qwen_cloud_api_key", "sk-test", raising=False)
    provider = QwenCloudProvider()

    import asyncio

    assert asyncio.run(provider.is_available()) is True


# ── Guarded live smoke ─────────────────────────────────────────────────────────


@pytest.mark.skipif(
    not (os.environ.get("QWEN_CLOUD_LIVE") == "1" and os.environ.get("DASHSCOPE_API_KEY")),
    reason="live smoke disabled (set QWEN_CLOUD_LIVE=1 and DASHSCOPE_API_KEY)",
)
def test_live_generate_smoke():
    import asyncio

    # Lazy import so collection works without the provider's network path.
    from chronocanvas.llm.providers.qwen_cloud import QwenCloudProvider

    provider = QwenCloudProvider()
    resp = asyncio.run(provider.generate("ping", max_tokens=16))
    assert resp.content.strip()
    assert resp.provider == "qwen-cloud"
