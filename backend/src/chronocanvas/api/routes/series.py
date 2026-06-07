"""Series Brain API (PRD §8, TRD §10)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.api.schemas.series import CanonOut, SeriesCreate, SeriesOut
from chronocanvas.db.engine import get_session
from chronocanvas.showrunner.series.service import CanonService

router = APIRouter(prefix="/series", tags=["series"])


@router.post("", response_model=SeriesOut, status_code=201)
async def create_series(body: SeriesCreate, session: AsyncSession = Depends(get_session)):
    svc = CanonService(session)
    series = await svc.create_series(
        title=body.title, premise=body.premise, era=body.era,
        creative_rules=body.creative_rules,
    )
    await session.commit()
    return series


@router.get("", response_model=list[SeriesOut])
async def list_series(session: AsyncSession = Depends(get_session)):
    return await CanonService(session).list_series()


@router.get("/{series_id}", response_model=SeriesOut)
async def get_series(series_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    series = await CanonService(session).get_series(series_id)
    if series is None:
        raise HTTPException(status_code=404, detail="series not found")
    return series


@router.get("/{series_id}/canon", response_model=CanonOut)
async def get_canon(series_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    svc = CanonService(session)
    if await svc.get_series(series_id) is None:
        raise HTTPException(status_code=404, detail="series not found")
    canon = await svc.get_canon(series_id)
    return CanonOut(series_id=series_id, **canon)
