"""Schemas for the Cost & Budgeting API (TRD §6, §11)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class BudgetOut(BaseModel):
    scope: str
    scope_id: uuid.UUID
    limit_usd: float
    soft_pct: float
    hard_behavior: str
    spent_usd: float
    reserved_usd: float
    available_usd: float

    model_config = {"from_attributes": True}


class BudgetUpdate(BaseModel):
    limit_usd: float | None = Field(default=None, ge=0)
    soft_pct: float | None = Field(default=None, ge=0, le=1)
    hard_behavior: str | None = None  # block|warn


class CostRollupOut(BaseModel):
    episode_id: uuid.UUID
    skill_cost_usd: float
    skill_calls: int
    media_cost_usd: float
    media_jobs: int
    total_usd: float
    confidence: str


class EstimateRequest(BaseModel):
    num_skill_calls: int = 0
    num_images: int = 0
    num_video_seconds: int = 0
    num_tts_chars: int = 0
    skill_model: str = "ollama/qwen2.5-coder:14b"


class EstimateOut(BaseModel):
    estimate_usd: float
    outcome: str  # allow|warn|block
    projected_usd: float
    limit_usd: float
