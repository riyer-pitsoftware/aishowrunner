"""Series Brain tests (TRD §10, §8.2) — pure logic, no database."""

from __future__ import annotations

import types

import pytest

from chronocanvas.showrunner.canon.immutability import (
    ImmutableRecordError,
    _block_committed_choice_update,
    _block_delete,
    _block_update,
    install_canon_guards,
)
from chronocanvas.showrunner.canon.state import MutationType, apply_mutation, fold
from chronocanvas.showrunner.episodes.state import (
    EpisodeStatus,
    InvalidTransitionError,
    assert_transition,
    can_transition,
    next_required_gate,
)


class _Mut:
    """Duck-typed mutation for fold tests."""

    def __init__(self, mtype, key=None, payload=None, seq=0, episode_id=None):
        self.mutation_type = mtype
        self.target_key = key
        self.payload = payload or {}
        self.provenance = {}
        self.episode_id = episode_id
        self.seq = seq
        self.created_at = seq


# ── Canon fold (asr-63f.3) ───────────────────────────────────────────────────

def test_fold_builds_and_retires_facts():
    muts = [
        _Mut("add_fact", "raja", {"text": "Rajaraja rules", "category": "ruler"}, seq=1),
        _Mut("add_fact", "fleet", {"text": "Chola fleet sails", "category": "military"}, seq=2),
        _Mut("update_fact", "raja", {"text": "Rajaraja I rules from Thanjavur"}, seq=3),
        _Mut("retire_fact", "fleet", seq=4),
    ]
    canon = fold(muts).to_dict()
    facts = {f["key"]: f for f in canon["facts"]}
    assert "raja" in facts and facts["raja"]["text"] == "Rajaraja I rules from Thanjavur"
    assert "fleet" not in facts  # retired -> excluded from current canon
    assert canon["applied"] == 4


def test_fold_threads_open_and_resolve():
    muts = [
        _Mut("open_thread", "spy", {"title": "Who is the spy?"}, seq=1),
        _Mut("open_thread", "debt", {"title": "The temple debt"}, seq=2),
        _Mut("resolve_thread", "spy", {"resolution": "The minister"}, seq=3),
    ]
    threads = fold(muts).to_dict()["threads"]
    assert [t["key"] for t in threads["open"]] == ["debt"]
    assert [t["key"] for t in threads["resolved"]] == ["spy"]


def test_fold_is_order_independent_via_seq():
    muts = [
        _Mut("retire_fact", "x", seq=2),
        _Mut("add_fact", "x", {"text": "exists"}, seq=1),
    ]
    # provided out of order; fold sorts by (created_at, seq)
    canon = fold(muts).to_dict()
    assert all(f["key"] != "x" for f in canon["facts"])  # added then retired


def test_fold_skips_unknown_mutation_type():
    state = fold([_Mut("teleport_character", "a", {})])
    assert state.applied == 0 and state.skipped == 1


def test_fold_attaches_episode_provenance():
    canon = fold([_Mut("add_fact", "k", {"text": "t"}, episode_id="ep-1")]).to_dict()
    assert canon["facts"][0]["origin"]["episode_id"] == "ep-1"


def test_mutationtype_values_stable():
    assert MutationType.ADD_FACT.value == "add_fact"
    assert apply_mutation.__name__ == "apply_mutation"


# ── Episode state machine (TRD §8.2) ─────────────────────────────────────────

def test_happy_path_transitions():
    seq = [
        (EpisodeStatus.DRAFT, EpisodeStatus.STORY_ROOM),
        (EpisodeStatus.STORY_ROOM, EpisodeStatus.BRANCH_GREENLIGHT),
        (EpisodeStatus.BRANCH_GREENLIGHT, EpisodeStatus.EPISODE_PLAN),
        (EpisodeStatus.EPISODE_PLAN, EpisodeStatus.EPISODE_GREENLIGHT),
        (EpisodeStatus.EPISODE_GREENLIGHT, EpisodeStatus.PRODUCING),
        (EpisodeStatus.PRODUCING, EpisodeStatus.FINAL_CUT),
        (EpisodeStatus.FINAL_CUT, EpisodeStatus.CANON_COMMIT),
        (EpisodeStatus.CANON_COMMIT, EpisodeStatus.DONE),
    ]
    for cur, nxt in seq:
        assert can_transition(cur, nxt)
        assert assert_transition(cur, nxt) is nxt


def test_reconsider_and_revise_loops():
    assert can_transition(EpisodeStatus.BRANCH_GREENLIGHT, EpisodeStatus.STORY_ROOM)
    assert can_transition(EpisodeStatus.EPISODE_GREENLIGHT, EpisodeStatus.EPISODE_PLAN)
    assert can_transition(EpisodeStatus.FINAL_CUT, EpisodeStatus.PRODUCING)


def test_invalid_transition_raises():
    with pytest.raises(InvalidTransitionError):
        assert_transition(EpisodeStatus.DRAFT, EpisodeStatus.PRODUCING)


def test_transition_accepts_raw_strings():
    assert assert_transition("draft", "story_room") is EpisodeStatus.STORY_ROOM


def test_next_required_gate():
    assert next_required_gate(EpisodeStatus.BRANCH_GREENLIGHT) == "branch"
    assert next_required_gate(EpisodeStatus.EPISODE_GREENLIGHT) == "episode"
    assert next_required_gate(EpisodeStatus.FINAL_CUT) == "final"
    assert next_required_gate(EpisodeStatus.PRODUCING) is None


# ── Immutability guards (TRD §10.2, §8.3) ────────────────────────────────────

def test_block_update_and_delete_raise():
    target = types.SimpleNamespace(id="abc")
    with pytest.raises(ImmutableRecordError):
        _block_update(None, None, target)
    with pytest.raises(ImmutableRecordError):
        _block_delete(None, None, target)


def test_selected_choice_is_frozen():
    selected = types.SimpleNamespace(
        _sa_instance_state=types.SimpleNamespace(committed_state={"selected": True})
    )
    with pytest.raises(ImmutableRecordError):
        _block_committed_choice_update(None, None, selected)
    # not-yet-selected choice may still be edited
    unselected = types.SimpleNamespace(
        _sa_instance_state=types.SimpleNamespace(committed_state={"selected": False})
    )
    _block_committed_choice_update(None, None, unselected)  # no raise


def test_install_canon_guards_registers_listeners():
    from sqlalchemy import event

    from chronocanvas.db.models.showrunner_series import CanonMutation

    install_canon_guards()
    install_canon_guards()  # idempotent
    assert event.contains(CanonMutation, "before_update", _block_update)
    assert event.contains(CanonMutation, "before_delete", _block_delete)


# ── Model registration (asr-63f.1) ───────────────────────────────────────────

def test_all_showrunner_tables_registered():
    import chronocanvas.db.models  # noqa: F401  (registers everything)
    from chronocanvas.db.base import Base

    tables = set(Base.metadata.tables)
    for t in (
        "series", "characters", "relationships", "canon_facts", "story_threads",
        "canon_mutations", "episodes", "branch_proposals", "beats",
        "audience_choices", "shots", "production_artifacts", "skill_invocations",
        "skill_contributions", "specialist_disagreements", "approval_gates",
    ):
        assert t in tables, f"missing table: {t}"
