"""Shot dependency DAG helpers (TRD §9.1, §9.3)."""

import pytest

from chronocanvas.showrunner.media.dag import (
    CycleError,
    stale_closure,
    topo_order,
    upstream_closure,
)


def test_topo_order_respects_dependencies():
    # c depends on b depends on a; d is independent
    deps = {"a": [], "b": ["a"], "c": ["b"], "d": []}
    order = topo_order(deps)
    assert order.index("a") < order.index("b") < order.index("c")
    assert set(order) == {"a", "b", "c", "d"}


def test_topo_order_is_deterministic_by_insertion():
    deps = {"a": [], "b": [], "c": []}
    assert topo_order(deps) == ["a", "b", "c"]


def test_topo_order_diamond():
    # a -> b, a -> c, both -> d
    deps = {"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]}
    order = topo_order(deps)
    assert order[0] == "a"
    assert order[-1] == "d"


def test_topo_order_detects_cycle():
    deps = {"a": ["b"], "b": ["a"]}
    with pytest.raises(CycleError):
        topo_order(deps)


def test_dangling_dependency_is_treated_as_satisfied():
    # b depends on unknown 'x' — x is auto-added as a satisfied root, no crash
    deps = {"b": ["x"]}
    order = topo_order(deps)
    assert order.index("x") < order.index("b")


def test_stale_closure_includes_changed_and_dependents():
    deps = {"a": [], "b": ["a"], "c": ["b"], "d": []}
    # changing a invalidates a, b, c — not d
    assert stale_closure(deps, "a") == {"a", "b", "c"}


def test_stale_closure_leaf_only_self():
    deps = {"a": [], "b": ["a"], "c": ["b"]}
    assert stale_closure(deps, "c") == {"c"}


def test_stale_closure_diamond():
    deps = {"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]}
    assert stale_closure(deps, "b") == {"b", "d"}
    assert stale_closure(deps, "a") == {"a", "b", "c", "d"}


def test_upstream_closure():
    deps = {"a": [], "b": ["a"], "c": ["b"], "d": ["b", "c"]}
    assert upstream_closure(deps, "d") == {"a", "b", "c"}
    assert upstream_closure(deps, "a") == set()
