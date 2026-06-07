"""Series + canon service (TRD §10). Canon is read by folding the mutation log;
mutations are appended, never updated."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.db.models.showrunner_series import CanonMutation, Series
from chronocanvas.showrunner.canon.state import fold


class CanonService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_series(
        self,
        *,
        title: str,
        premise: str | None = None,
        era: str | None = None,
        creative_rules: dict | None = None,
    ) -> Series:
        series = Series(
            title=title, premise=premise, era=era, creative_rules=creative_rules or {}
        )
        self.session.add(series)
        await self.session.flush()
        return series

    async def list_series(self) -> list[Series]:
        rows = await self.session.execute(select(Series).order_by(Series.created_at.desc()))
        return list(rows.scalars().all())

    async def get_series(self, series_id: uuid.UUID) -> Series | None:
        return await self.session.get(Series, series_id)

    async def append_mutation(
        self,
        *,
        series_id: uuid.UUID,
        mutation_type: str,
        target_key: str | None = None,
        target_type: str | None = None,
        payload: dict | None = None,
        provenance: dict | None = None,
        episode_id: uuid.UUID | None = None,
        choice_id: uuid.UUID | None = None,
        source_skill: str | None = None,
        seq: int = 0,
    ) -> CanonMutation:
        m = CanonMutation(
            series_id=series_id, episode_id=episode_id, choice_id=choice_id, seq=seq,
            mutation_type=mutation_type, target_type=target_type, target_key=target_key,
            payload=payload or {}, provenance=provenance or {}, source_skill=source_skill,
        )
        self.session.add(m)
        await self.session.flush()
        return m

    async def get_canon(self, series_id: uuid.UUID) -> dict[str, Any]:
        rows = await self.session.execute(
            select(CanonMutation).where(CanonMutation.series_id == series_id)
        )
        return fold(list(rows.scalars().all())).to_dict()
