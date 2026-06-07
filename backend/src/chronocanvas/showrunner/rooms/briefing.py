"""Canon briefing — the context every room receives (PRD §5.2 step 1)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession


def format_briefing(series: dict, canon: dict) -> str:
    """Render a compact canon briefing (pure)."""
    lines = ["# Series briefing", f"**Title:** {series.get('title', '?')}"]
    if series.get("era"):
        lines.append(f"**Era:** {series['era']}")
    if series.get("premise"):
        lines.append(f"**Premise:** {series['premise']}")

    facts = canon.get("facts", [])
    lines.append(f"\n## Canon facts ({len(facts)})")
    for f in facts[:30]:
        lines.append(f"- {f.get('text', '')}")

    threads = canon.get("threads", {})
    open_threads = threads.get("open", []) if isinstance(threads, dict) else []
    lines.append(f"\n## Open story threads ({len(open_threads)})")
    for t in open_threads[:20]:
        lines.append(f"- {t.get('title', '')}")

    chars = canon.get("characters", [])
    if chars:
        lines.append(f"\n## Characters ({len(chars)})")
        for c in chars[:20]:
            name = c.get("name") or c.get("key", "")
            lines.append(f"- {name}")
    return "\n".join(lines)


async def build_briefing(session: AsyncSession, series_id: uuid.UUID) -> str:
    from chronocanvas.showrunner.series.service import CanonService

    svc = CanonService(session)
    series = await svc.get_series(series_id)
    series_dict = (
        {"title": series.title, "era": series.era, "premise": series.premise}
        if series
        else {}
    )
    canon = await svc.get_canon(series_id)
    return format_briefing(series_dict, canon)
