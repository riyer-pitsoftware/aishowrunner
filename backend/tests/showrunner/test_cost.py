"""Cost & Budgeting tests (TRD §6) — pure pricing, budget evaluation, estimation."""

from __future__ import annotations

import pytest

from chronocanvas.showrunner.cost.budget import (
    BudgetExceeded,
    estimate_production,
    evaluate,
)
from chronocanvas.showrunner.cost.pricing import (
    media_cost,
    price_skill_result,
    split_model,
    text_cost,
)

# A pricing dict with real (nonzero) numbers for deterministic assertions.
PRICING = {
    "text": {
        "ollama": {"input_per_1m": 0.0, "output_per_1m": 0.0},
        "qwen-cloud": {
            "default": {"input_per_1m": 1.0, "output_per_1m": 2.0},
            "qwen-max": {"input_per_1m": 10.0, "output_per_1m": 30.0},
        },
    },
    "media": {
        "image": {"unit": "per_image", "price": 0.05},
        "video": {"unit": "per_second", "price": 0.20},
        "tts": {"unit": "per_1k_chars", "price": 0.015},
    },
    "estimate": {"avg_skill_input_tokens": 1000, "avg_skill_output_tokens": 500},
}


# ── Pricing (asr-3mk.1/.2) ───────────────────────────────────────────────────

def test_split_model():
    assert split_model("qwen-cloud/qwen-plus") == ("qwen-cloud", "qwen-plus")
    assert split_model("ollama") == ("ollama", "")


def test_ollama_is_free():
    assert text_cost("ollama/qwen2.5-coder:14b", 1_000_000, 1_000_000, PRICING) == 0.0


def test_qwen_cloud_default_and_model_rates():
    # default: 1/1M in + 2/1M out
    assert text_cost("qwen-cloud/qwen-plus", 1_000_000, 1_000_000, PRICING) == pytest.approx(3.0)
    # qwen-max override: 10 in + 30 out
    assert text_cost("qwen-cloud/qwen-max", 1_000_000, 1_000_000, PRICING) == pytest.approx(40.0)


def test_unknown_provider_is_free():
    assert text_cost("mystery/model", 5_000_000, 5_000_000, PRICING) == 0.0


def test_media_cost_units():
    assert media_cost("image", 4, PRICING) == (0.05, pytest.approx(0.20))
    assert media_cost("video", 8, PRICING) == (0.20, pytest.approx(1.60))
    assert media_cost("tts", 2000, PRICING) == (0.015, pytest.approx(0.03))  # per 1k chars


def test_price_skill_result_confidence():
    cost, conf = price_skill_result("ollama/x", 100, 50, tokens_estimated=True, pricing=PRICING)
    assert cost == 0.0 and conf == "estimated"
    cost2, conf2 = price_skill_result("qwen-cloud/qwen-plus", 1_000_000, 0, False, PRICING)
    assert cost2 == pytest.approx(1.0) and conf2 == "exact"


# ── Budget evaluation (asr-3mk.4/.6) ─────────────────────────────────────────

def test_evaluate_allow_warn_block():
    # limit 10, soft 0.8 -> warn at >=8
    assert evaluate(10, 0, 0, 5).outcome == "allow"
    assert evaluate(10, 7, 0, 1).outcome == "warn"   # projected 8 == soft
    assert evaluate(10, 9, 0, 2).outcome == "block"  # projected 11 > 10, hard block


def test_evaluate_warn_behavior_does_not_block():
    c = evaluate(10, 9, 0, 5, hard_behavior="warn")
    assert c.over_hard is True and c.outcome == "warn"


def test_evaluate_uncapped_limit_always_allows():
    assert evaluate(0, 1000, 1000, 1000).outcome == "allow"


def test_evaluate_counts_reserved():
    # spent 4 + reserved 4 + amount 3 = 11 > 10
    assert evaluate(10, 4, 4, 3).outcome == "block"


def test_budget_exceeded_carries_check():
    c = evaluate(1, 0, 0, 5)
    err = BudgetExceeded(c)
    assert err.check.over_hard and c.as_error()["error"] == "budget_exceeded"


# ── Estimator (asr-3mk.5) ────────────────────────────────────────────────────

def test_estimate_production_is_deterministic():
    # 3 skill calls on free ollama -> 0; + 10 images @0.05 + 8s video @0.20 + 600 tts chars @0.015
    est = estimate_production(
        num_skill_calls=3, num_images=10, num_video_seconds=8, num_tts_chars=600,
        skill_model="ollama/x", pricing=PRICING,
    )
    # images 0.5 + video 1.6 + tts 0.009 = 2.109
    assert est == pytest.approx(2.109)


def test_estimate_skill_cost_on_cloud():
    est = estimate_production(
        num_skill_calls=2, skill_model="qwen-cloud/qwen-plus", pricing=PRICING,
    )
    # per call: 1000/1e6*1 + 500/1e6*2 = 0.001 + 0.001 = 0.002 ; x2 = 0.004
    assert est == pytest.approx(0.004)


# ── Model registration (asr-3mk.3) ───────────────────────────────────────────

def test_cost_tables_registered():
    import chronocanvas.db.models  # noqa: F401
    from chronocanvas.db.base import Base

    for t in ("media_generations", "budgets", "budget_reservations"):
        assert t in Base.metadata.tables
