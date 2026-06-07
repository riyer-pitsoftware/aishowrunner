"""Pydantic schemas for the Series Brain API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SeriesCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    premise: str | None = None
    era: str | None = None
    creative_rules: dict | None = None


class SeriesOut(BaseModel):
    id: uuid.UUID
    title: str
    premise: str | None = None
    era: str | None = None
    creative_rules: dict | None = None
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CanonOut(BaseModel):
    series_id: uuid.UUID
    facts: list[dict]
    characters: list[dict]
    relationships: list[dict]
    threads: dict
    applied: int
