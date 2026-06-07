"""Showrunner room tests (TRD §8) — pure cores: comparator, gates, requests,
briefing, events. DB orchestration is covered by the pg integration test."""

from __future__ import annotations

import pytest

from chronocanvas.showrunner.episodes.state import EpisodeStatus, InvalidTransitionError
from chronocanvas.showrunner.rooms.briefing import format_briefing
from chronocanvas.showrunner.rooms.definitions import ROOMS, build_requests
from chronocanvas.showrunner.rooms.disagreement import detect_disagreements, summarize
from chronocanvas.showrunner.rooms.events import EventType, channel_for, event_payload
from chronocanvas.showrunner.rooms.gates import gate_target, idempotent_transition

# ── Disagreement comparator (asr-n88.6) ──────────────────────────────────────

def _c(skill, stance, **fields):
    return {"skill_name": skill, "stance": stance, "fields": fields}


def test_agreement_yields_no_disagreement():
    contribs = [_c("team-creative-director", "support"), _c("team-historian", "support")]
    assert detect_disagreements(contribs, "d1") == []


def test_mixed_stance_flags_disagreement():
    contribs = [_c("team-creative-director", "support"), _c("team-narrative-engineer", "concern")]
    out = detect_disagreements(contribs, "d1")
    assert len(out) == 1 and out[0]["axis"] == "stance"
    assert out[0]["stances"]["team-narrative-engineer"] == "concern"


def test_any_block_flags_even_single_voice():
    out = detect_disagreements([_c("pessimism", "block")], "d1")
    assert len(out) == 1 and "block" in out[0]["detail"].lower()


def test_field_conflict_historian_vs_support():
    contribs = [
        _c("team-historian", "concern", accuracy="fiction"),
        _c("team-creative-director", "support"),
    ]
    out = detect_disagreements(contribs, "d1")
    axes = {d["axis"] for d in out}
    assert "historical_accuracy" in axes  # historian flagged fiction while CD supported


def test_no_false_consensus_unknown_only():
    # two unknowns -> nothing to compare, no synthetic agreement
    assert detect_disagreements([_c("a", "unknown"), _c("b", "unknown")], "d") == []


def test_summarize_tally():
    s = summarize([_c("a", "support"), _c("b", "support"), _c("c", "block")])
    assert s["stance_tally"]["support"] == 2 and s["stance_tally"]["block"] == 1


# ── Gate mapping + idempotent transitions (asr-n88.4/.5) ──────────────────────

def test_gate_forward_targets():
    assert gate_target("branch", "approved") is EpisodeStatus.EPISODE_PLAN
    assert gate_target("episode", "approved") is EpisodeStatus.PRODUCING
    assert gate_target("final", "approved") is EpisodeStatus.CANON_COMMIT


def test_gate_loopback_on_reconsider():
    assert gate_target("branch", "reconsider") is EpisodeStatus.STORY_ROOM
    assert gate_target("episode", "revise") is EpisodeStatus.EPISODE_PLAN
    assert gate_target("final", "reduce") is EpisodeStatus.PRODUCING


def test_gate_kill_no_transition():
    assert gate_target("branch", "kill") is None


def test_unknown_gate_raises():
    with pytest.raises(ValueError):
        gate_target("bogus", "approved")


def test_idempotent_transition_noop_when_same():
    same = idempotent_transition(EpisodeStatus.PRODUCING, EpisodeStatus.PRODUCING)
    assert same is EpisodeStatus.PRODUCING


def test_idempotent_transition_validates():
    fwd = idempotent_transition(EpisodeStatus.DRAFT, EpisodeStatus.STORY_ROOM)
    assert fwd is EpisodeStatus.STORY_ROOM
    with pytest.raises(InvalidTransitionError):
        idempotent_transition(EpisodeStatus.DRAFT, EpisodeStatus.PRODUCING)


# ── Room rosters + request building (asr-n88.1/.2/.3) ────────────────────────

def test_rosters_match_prd():
    assert ROOMS["story_room"].skills == (
        "team-creative-director", "team-narrative-engineer",
        "team-historian", "team-game-designer",
    )
    assert len(ROOMS["production_desk"].skills) == 6
    assert ROOMS["greenlight"].skills == ("team-pm", "team-judge-panel", "pessimism")


def test_build_requests_one_per_skill_with_focus():
    reqs = build_requests(
        ROOMS["story_room"], briefing="BRIEF", task="TASK",
        series_id="s1", episode_id="e1", decision_id="d1",
    )
    assert len(reqs) == 4
    assert all(r.room == "story_room" and r.structured for r in reqs)
    hist = next(r for r in reqs if r.skill_name == "team-historian")
    assert "BRIEF" in hist.message and "TASK" in hist.message
    assert "fields.accuracy" in hist.message  # focus line present


# ── Briefing + events ────────────────────────────────────────────────────────

def test_format_briefing_includes_canon():
    series = {"title": "The Thanjavur Ledger", "era": "Chola 10th c.", "premise": "P"}
    canon = {
        "facts": [{"text": "Rajaraja rules"}],
        "threads": {"open": [{"title": "The missing tribute"}], "resolved": []},
        "characters": [{"name": "Arul"}],
    }
    b = format_briefing(series, canon)
    assert "Thanjavur Ledger" in b and "Rajaraja rules" in b
    assert "missing tribute" in b and "Arul" in b


def test_event_payload_and_channel():
    p = event_payload(EventType.GATE_DECIDED, gate="episode", verdict="approved")
    assert p["type"] == "gate_decided" and p["gate"] == "episode"
    assert channel_for("e1") == "episode:e1"
