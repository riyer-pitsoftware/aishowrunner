"""Seed loader entrypoint — ``python -m chronocanvas.seed.load_seed``.

Loads the showrunner historical-noir demo series (PRD §9.3.7) into the
configured database so the three rooms have real data to operate on during
UAT/demo. Idempotent: re-running does not duplicate the series.

This is distinct from the chrono timeline seed (``seed/load_seed.py`` at the
repo root, run by ``make seed`` inside the API container), which loads periods
and historical figures and is left untouched. ``make seed-local`` points here.

Canon rows are append-only and have ORM immutability guards installed at app
startup (``main.lifespan``). This loader opens its own session against a fresh
engine — the guards are not installed in a bare seed process — and the seeder
only ever *creates* canon rows, never updates them, so it is safe either way.
"""

from __future__ import annotations

import asyncio

from chronocanvas.db.engine import async_session
from chronocanvas.seed.showrunner_demo import seed_showrunner_demo


async def main() -> None:
    print("Loading showrunner demo seed...")
    async with async_session() as session:
        series = await seed_showrunner_demo(session)
        await session.commit()
    print(f"  Demo series ready: {series.title!r} ({series.era})")
    print("Showrunner demo seed loaded.")


if __name__ == "__main__":
    asyncio.run(main())
