"""Canon fold — rebuild current series state from the ordered mutation log.

Pure functions over duck-typed mutations (anything with ``mutation_type``,
``target_key``, ``payload``, ``provenance``, ``created_at``, ``seq``). The DB row
``CanonMutation`` satisfies this, and so do plain test objects. Current canon is
``fold(mutations)`` — the log is the source of truth (TRD §10.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class MutationType(str, Enum):
    ADD_FACT = "add_fact"
    UPDATE_FACT = "update_fact"
    RETIRE_FACT = "retire_fact"
    ADD_CHARACTER = "add_character"
    UPDATE_CHARACTER = "update_character"
    SET_RELATIONSHIP = "set_relationship"
    END_RELATIONSHIP = "end_relationship"
    OPEN_THREAD = "open_thread"
    RESOLVE_THREAD = "resolve_thread"


@dataclass
class CanonState:
    facts: dict[str, dict] = field(default_factory=dict)
    characters: dict[str, dict] = field(default_factory=dict)
    relationships: dict[str, dict] = field(default_factory=dict)
    threads: dict[str, dict] = field(default_factory=dict)
    applied: int = 0
    skipped: int = 0  # unknown mutation types (forward-compat)

    def to_dict(self) -> dict[str, Any]:
        return {
            "facts": [f for f in self.facts.values() if f.get("status") != "retired"],
            "characters": list(self.characters.values()),
            "relationships": [
                r for r in self.relationships.values() if r.get("status") == "active"
            ],
            "threads": {
                "open": [t for t in self.threads.values() if t.get("status") == "open"],
                "resolved": [t for t in self.threads.values() if t.get("status") == "resolved"],
            },
            "applied": self.applied,
        }


def _key(m: Any) -> str | None:
    return getattr(m, "target_key", None) or (getattr(m, "payload", None) or {}).get("key")


def _payload(m: Any) -> dict:
    return getattr(m, "payload", None) or {}


def _provenance(m: Any) -> dict:
    prov = getattr(m, "provenance", None) or {}
    ep = getattr(m, "episode_id", None)
    if ep is not None and "episode_id" not in prov:
        prov = {**prov, "episode_id": str(ep)}
    return prov


def apply_mutation(state: CanonState, m: Any) -> CanonState:
    """Apply one mutation in place. Unknown types are skipped (not fatal)."""
    try:
        mt = MutationType(getattr(m, "mutation_type", None))
    except ValueError:
        state.skipped += 1
        return state

    key = _key(m)
    payload = _payload(m)
    prov = _provenance(m)

    if mt is MutationType.ADD_FACT and key:
        state.facts[key] = {
            "key": key, "category": payload.get("category"),
            "text": payload.get("text", ""), "status": "active", "origin": prov,
        }
    elif mt is MutationType.UPDATE_FACT and key in state.facts:
        if "text" in payload:
            state.facts[key]["text"] = payload["text"]
        if "category" in payload:
            state.facts[key]["category"] = payload["category"]
    elif mt is MutationType.RETIRE_FACT and key in state.facts:
        state.facts[key]["status"] = "retired"
    elif mt is MutationType.ADD_CHARACTER and key:
        state.characters[key] = {"key": key, **payload, "origin": prov}
    elif mt is MutationType.UPDATE_CHARACTER and key in state.characters:
        state.characters[key].update(payload)
    elif mt is MutationType.SET_RELATIONSHIP and key:
        state.relationships[key] = {"key": key, **payload, "status": "active", "origin": prov}
    elif mt is MutationType.END_RELATIONSHIP and key in state.relationships:
        state.relationships[key]["status"] = "ended"
    elif mt is MutationType.OPEN_THREAD and key:
        state.threads[key] = {
            "key": key, "title": payload.get("title", ""), "status": "open", "origin": prov,
        }
    elif mt is MutationType.RESOLVE_THREAD and key in state.threads:
        state.threads[key]["status"] = "resolved"
        state.threads[key]["resolution"] = payload.get("resolution")
    else:
        state.skipped += 1
        return state

    state.applied += 1
    return state


def _order(m: Any):
    return (getattr(m, "created_at", None) or 0, getattr(m, "seq", 0) or 0)


def fold(mutations: Iterable[Any]) -> CanonState:
    """Fold an unordered iterable of mutations into the current CanonState."""
    state = CanonState()
    for m in sorted(mutations, key=_order):
        apply_mutation(state, m)
    return state
