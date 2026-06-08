"""Shot dependency DAG (TRD §9.1, §9.3) — pure graph helpers.

A shot declares ``depends_on`` (a list of upstream shot ids). These functions
operate on a plain ``deps`` mapping (``shot_id -> list[upstream_id]``) so they are
testable without a DB. Callers build the mapping from ``Shot`` rows.

Two operations drive production:
- ``topo_order`` — the order shots may be generated (upstream before downstream).
- ``stale_closure`` — when a shot changes, the set of shots that must regenerate
  (the shot itself plus everything that transitively depends on it).
"""

from __future__ import annotations

from collections import deque
from typing import Hashable, TypeVar

H = TypeVar("H", bound=Hashable)


class CycleError(ValueError):
    """The shot dependency graph contains a cycle — not a DAG."""


def _normalize(deps: dict[H, list[H]]) -> dict[H, list[H]]:
    """Ensure every referenced node appears as a key; drop dangling edges' weight
    by keeping them (a dependency on an unknown id is treated as already-satisfied
    so production is never wedged by a stale reference)."""
    nodes: dict[H, list[H]] = {n: list(ups or []) for n, ups in deps.items()}
    for ups in list(nodes.values()):
        for u in ups:
            nodes.setdefault(u, [])
    return nodes


def topo_order(deps: dict[H, list[H]]) -> list[H]:
    """Return shot ids in dependency order (Kahn). Raises CycleError on a cycle.

    Ties are broken deterministically by insertion order of the input mapping so
    repeated runs produce identical plans.
    """
    nodes = _normalize(deps)
    order_hint = {n: i for i, n in enumerate(nodes)}
    indeg: dict[H, int] = {n: 0 for n in nodes}
    for n, ups in nodes.items():
        # n depends on each up → edge up -> n; n's indegree = number of upstreams
        indeg[n] = len(ups)

    ready = sorted((n for n, d in indeg.items() if d == 0), key=lambda n: order_hint[n])
    queue: deque[H] = deque(ready)
    # downstream adjacency: up -> [nodes depending on up]
    downstream: dict[H, list[H]] = {n: [] for n in nodes}
    for n, ups in nodes.items():
        for u in ups:
            downstream[u].append(n)

    out: list[H] = []
    while queue:
        n = queue.popleft()
        out.append(n)
        nxt = []
        for m in downstream[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                nxt.append(m)
        for m in sorted(nxt, key=lambda x: order_hint[x]):
            queue.append(m)

    if len(out) != len(nodes):
        remaining = [n for n in nodes if n not in set(out)]
        raise CycleError(f"shot dependency cycle among: {remaining}")
    return out


def stale_closure(deps: dict[H, list[H]], changed: H) -> set[H]:
    """Set of shots invalidated when ``changed`` is regenerated: ``changed`` plus
    every shot that transitively depends on it."""
    nodes = _normalize(deps)
    downstream: dict[H, list[H]] = {n: [] for n in nodes}
    for n, ups in nodes.items():
        for u in ups:
            downstream[u].append(n)

    seen: set[H] = set()
    stack = [changed]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(downstream.get(cur, []))
    return seen


def upstream_closure(deps: dict[H, list[H]], target: H) -> set[H]:
    """Set of shots ``target`` transitively depends on (excluding ``target``).

    Used to confirm prerequisites exist before (re)generating a shot.
    """
    nodes = _normalize(deps)
    seen: set[H] = set()
    stack = list(nodes.get(target, []))
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(nodes.get(cur, []))
    seen.discard(target)
    return seen
