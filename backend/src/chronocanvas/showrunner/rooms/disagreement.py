"""Disagreement detection (TRD §8.4) — deterministic, no LLM "consensus".

Given the contributions for a decision, flag where specialists diverge. The
system surfaces disagreements verbatim; it never averages or merges conflicting
reviews into a false consensus.

Two axes:
- **stance**: any `block`, or a mix of support/concern across specialists.
- **field conflicts**: declared incompatibilities, e.g. a historian marking a
  beat `fiction`/`inaccurate` while another specialist `support`s it.
"""

from __future__ import annotations

from typing import Any

# field-level conflict rules: (skill substring, fields path, bad values)
# kept data-driven so new axes are cheap to add.
_FIELD_CONFLICT_RULES = [
    {
        "skill": "historian",
        "field": "accuracy",
        "bad_values": {"fiction", "inaccurate", "anachronism", "false"},
        "axis": "historical_accuracy",
    },
]


def _norm_stance(c: dict) -> str:
    return str(c.get("stance") or "unknown").lower().strip()


def detect_disagreements(
    contributions: list[dict], decision_id: str | None = None
) -> list[dict]:
    """Return a list of disagreement records (dicts) for one decision.

    Each contribution: ``{"skill_name", "stance", "fields"}``. Returns [] when
    specialists agree. Never raises.
    """
    contribs = [c for c in contributions if c.get("skill_name")]
    if len(contribs) < 2 and not any(_norm_stance(c) == "block" for c in contribs):
        # a lone "block" still matters; otherwise <2 voices can't disagree
        if not any(_norm_stance(c) == "block" for c in contribs):
            return []

    out: list[dict] = []
    stances = {c["skill_name"]: _norm_stance(c) for c in contribs}
    distinct = {s for s in stances.values() if s != "unknown"}

    has_block = "block" in distinct
    mixed = len({s for s in distinct if s in {"support", "concern", "block"}}) > 1

    if has_block or mixed:
        out.append({
            "decision_id": decision_id,
            "axis": "stance",
            "stances": stances,
            "detail": _stance_detail(stances, has_block),
            "resolved": False,
        })

    # field-conflict axes
    for rule in _FIELD_CONFLICT_RULES:
        flaggers = [
            c["skill_name"]
            for c in contribs
            if rule["skill"] in c["skill_name"]
            and str((c.get("fields") or {}).get(rule["field"], "")).lower() in rule["bad_values"]
        ]
        supporters = [c["skill_name"] for c in contribs if _norm_stance(c) == "support"]
        if flaggers and supporters and set(flaggers) != set(supporters):
            out.append({
                "decision_id": decision_id,
                "axis": rule["axis"],
                "stances": stances,
                "detail": (
                    f"{', '.join(flaggers)} flagged {rule['field']} while "
                    f"{', '.join(supporters)} supported the decision."
                ),
                "resolved": False,
            })

    return out


def _stance_detail(stances: dict[str, str], has_block: bool) -> str:
    parts = [f"{skill}={stance}" for skill, stance in sorted(stances.items())]
    lead = "A specialist blocked: " if has_block else "Specialists diverge: "
    return lead + ", ".join(parts)


def summarize(contributions: list[dict]) -> dict[str, Any]:
    """Quick tally for UI/events."""
    tally: dict[str, int] = {}
    for c in contributions:
        tally[_norm_stance(c)] = tally.get(_norm_stance(c), 0) + 1
    return {"stance_tally": tally, "count": len(contributions)}
