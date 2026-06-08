#!/usr/bin/env python3
"""submission_gate.py — AI Showrunner submission gate (bead asr-av5.6).

PRD §10 gates the hackathon submission on two independent checks:

  1. PESSIMISM gate — the ``pessimism`` skill reviews the project's *completion
     claims* (the sprint-acceptance doc UAT-7 + git log + closed beads) and the
     gate FAILS if any unsupported "done/complete" claim is flagged.

  2. JUDGE-PANEL gate — the ``team-judge-panel`` skill scores the deliverable
     summary against the hackathon rubric and the gate FAILS unless the verdict
     is passing.

The gate invokes the skills through the *same mechanism the app uses* — it shells
out to the canonical agentic-harness runtime ``runtime/run_skill.py`` (the path
modelled by ``chronocanvas.showrunner.skills.subprocess_port.SubprocessSkillPort``),
piping the claims/summary on stdin and passing the resolved ``--model`` from
``.harness/models.yaml`` so routing matches the product.

It NEVER fabricates a PASS. If the harness, ``uv``, or Ollama is unavailable the
relevant gate reports SKIP (with a clear warning) — it does not pass and it does
not crash. The overall exit code is 0 only when every *run* gate passed and no
gate failed.

Exit codes:
    0   all run gates passed (skips allowed, see --strict)
    1   at least one gate FAILED (or a SKIP under --strict, or usage error)

Usage:
    python scripts/submission_gate.py                 # both gates
    python scripts/submission_gate.py --pessimism-only
    python scripts/submission_gate.py --judge-only
    python scripts/submission_gate.py --strict        # treat SKIP as failure

Configuration (env overrides flags-default-from-repo):
    HARNESS_REPO          default ~/code/agentic-harness
    SKILL_PORT            "subprocess" (only supported mode here) — informational
    SHOWRUNNER_MODELS     default <repo>/.harness/models.yaml
    SUBMISSION_MODEL      explicit PROVIDER/MODEL override (skips tier lookup)
    SKILL_TIMEOUT_S       default 180
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths / defaults (mirror chronocanvas.config defaults; see skills/__init__.py)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HARNESS_REPO = Path.home() / "code" / "agentic-harness"
DEFAULT_MODELS_YAML = REPO_ROOT / ".harness" / "models.yaml"

PESSIMISM_SKILL = "pessimism"
JUDGE_SKILL = "team-judge-panel"

# Critic tier backs both adversarial skills (see .harness/models.yaml CRITIC CAVEAT).
SKILL_MODEL_TIER = "critic"

UAT7 = REPO_ROOT / "docs" / "uat" / "suites" / "UAT-7-sprint-acceptance.md"


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


@dataclass
class GateResult:
    name: str
    status: str  # PASS | FAIL | SKIP
    detail: str
    model: str = ""
    output: str = ""


# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------


def resolve_harness_repo() -> Path:
    return Path(os.environ.get("HARNESS_REPO") or DEFAULT_HARNESS_REPO)


def resolve_models_yaml() -> Path:
    return Path(os.environ.get("SHOWRUNNER_MODELS") or DEFAULT_MODELS_YAML)


def resolve_timeout() -> float:
    try:
        return float(os.environ.get("SKILL_TIMEOUT_S", "180"))
    except ValueError:
        return 180.0


def resolve_model() -> str | None:
    """Resolve the model the same way SubprocessSkillPort does: explicit override,
    else the critic tier from models.yaml. Returns None if neither is available
    (run_skill.py then falls back to the skill's own frontmatter / global yaml)."""
    explicit = os.environ.get("SUBMISSION_MODEL")
    if explicit:
        return explicit
    models_yaml = resolve_models_yaml()
    if not models_yaml.is_file():
        return None
    try:
        import yaml  # optional; degrade gracefully if absent

        cfg = yaml.safe_load(models_yaml.read_text()) or {}
        return cfg.get(SKILL_MODEL_TIER)
    except Exception:
        # No yaml available, or unparseable — let run_skill.py resolve.
        return None


# ---------------------------------------------------------------------------
# Environment probing (graceful degradation)
# ---------------------------------------------------------------------------


def preflight() -> tuple[bool, str]:
    """Return (ready, reason). ready=False means the harness substrate is not
    available; the caller should SKIP rather than crash."""
    harness = resolve_harness_repo()
    run_skill = harness / "runtime" / "run_skill.py"
    if not run_skill.is_file():
        return False, f"run_skill.py not found at {run_skill} (set HARNESS_REPO)"
    if shutil.which("uv") is None:
        return False, "`uv` not on PATH — run_skill.py needs it (PEP-723 inline deps)"
    return True, ""


def _ollama_reachable() -> bool:
    """Best-effort local Ollama probe. Only meaningful when the resolved model is
    an ollama/* tier; cloud models bypass this."""
    import urllib.request

    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Claim / summary assembly (the evidence base the skills review)
# ---------------------------------------------------------------------------


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        ).stdout.strip()
    except Exception:
        return ""


def _closed_beads() -> str:
    if shutil.which("bd") is None:
        return "(bd CLI unavailable — bead closures not enumerated)"
    try:
        out = subprocess.run(
            ["bd", "list", "--status", "closed"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        ).stdout.strip()
        return out or "(no closed beads reported)"
    except Exception:
        return "(bd list failed)"


def build_completion_claims() -> str:
    """The pessimism gate reviews these for unsupported done/complete claims."""
    uat = UAT7.read_text() if UAT7.is_file() else "(UAT-7 sprint-acceptance doc missing)"
    git_log = _git("log", "--oneline", "-30") or "(git log unavailable)"
    beads = _closed_beads()
    return f"""You are reviewing the COMPLETION CLAIMS for the AI Showrunner project
before hackathon submission. Apply your epistemic-hygiene standard strictly.

Your task: flag every claim of "done", "complete", "passing", "shipped", or
"verified" that is NOT backed by reproducible evidence in the material below
(observed test output, a runnable command, a committed artifact). Distinguish
"CODE COMPLETE / pending live-run" (honest) from "DONE" with no evidence
(unsupported). List each unsupported claim explicitly.

Respond with a final line of exactly one of:
    PESSIMISM-VERDICT: CLEAN        (no unsupported completion claims)
    PESSIMISM-VERDICT: FLAGGED      (one or more unsupported claims; list them)

=== SPRINT ACCEPTANCE (UAT-7) ===
{uat}

=== GIT LOG (recent) ===
{git_log}

=== CLOSED BEADS ===
{beads}
"""


def build_deliverable_summary() -> str:
    """The judge-panel gate scores this against the hackathon rubric."""
    return """You are the hackathon Judge Panel (Mara/UX, Ravi/Tech, Sofia/Demo).
Score the AI Showrunner submission against the AUTHORITATIVE hackathon rubric
below — NOT your default weights. Be skeptical; a missing hard requirement is an
instant disqualifier.

AUTHORITATIVE rubric weights (Qwen Cloud Hackathon, AI Showrunner / Track 2):
  - Technical Depth & Engineering      30%
  - Innovation & AI Creativity         30%
  - Problem Value & Impact             25%
  - Presentation & Documentation       15%

Hard requirements (all mandatory): Qwen models on Qwen Cloud; public OSS repo
with detectable license; proof of Alibaba Cloud deployment; architecture diagram;
demo video ~3 min; track identified (AI Showrunner).

WHAT THE PRODUCT DOES:
  AI Showrunner turns a series premise into produced 9:16 episodes. A Skill Plane
  runs role "skills" (creative director, narrative engineer, historian, line
  producer, PM, judges) as Qwen models via the agentic-harness; orchestration
  stays in the product (TRD: Skill Plane vs Media Plane). A Series Brain holds
  immutable canon (facts/threads, append-only, provenance). Showrunner Rooms
  (Story Room, Production Desk, Greenlight) convene skills, surface verbatim
  disagreement (dissent preserved, not averaged), and gate progression behind
  greenlights with per-node budget reserve/commit against a hard cap. The Media
  Plane generates each shot over a dependency DAG via Alibaba Wan (text-to-image
  / text-to-video) and CosyVoice/Qwen-TTS, supports selective regeneration that
  preserves approved shots, and assembles a final 9:16 cut. A cost ledger tracks
  real token + media spend. Qwen Cloud is load-bearing: disabling it breaks core
  skill intelligence and media generation.

Score each axis 0-100 with a one-line justification, compute the weighted total,
and give remediation notes for any weak axis. Conclude with a final line of
exactly one of:
    JUDGE-VERDICT: PASS            (weighted total clears the bar, no DQ)
    JUDGE-VERDICT: FAIL            (below bar or a hard requirement missing)
"""


# ---------------------------------------------------------------------------
# Skill invocation (subprocess → run_skill.py, matching SubprocessSkillPort)
# ---------------------------------------------------------------------------


def invoke_skill(skill: str, message: str) -> tuple[int, str, str]:
    """Run the skill via run_skill.py. Returns (returncode, stdout, stderr).
    returncode 127 is reserved here for 'could not even launch'."""
    harness = resolve_harness_repo()
    run_skill = harness / "runtime" / "run_skill.py"
    argv: list[str] = [str(run_skill), skill]
    model = resolve_model()
    if model:
        argv += ["--model", model]

    try:
        proc = subprocess.run(
            argv,
            input=message,
            capture_output=True,
            text=True,
            timeout=resolve_timeout(),
            cwd=REPO_ROOT,  # so .harness/models.yaml (project) is discovered
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {resolve_timeout():.0f}s"
    except Exception as e:  # noqa: BLE001
        return 127, "", str(e)


def _model_is_ollama() -> bool:
    m = resolve_model() or ""
    return m.startswith("ollama/") or m == ""  # empty → likely local default


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------


def run_pessimism_gate() -> GateResult:
    ready, reason = preflight()
    if not ready:
        return GateResult(PESSIMISM_SKILL, SKIP, f"harness unavailable: {reason}")
    if _model_is_ollama() and not _ollama_reachable():
        return GateResult(
            PESSIMISM_SKILL, SKIP,
            "Ollama not reachable (local critic model) — start `ollama serve` or set SUBMISSION_MODEL",
        )

    rc, out, err = invoke_skill(PESSIMISM_SKILL, build_completion_claims())
    model = resolve_model() or "(skill/global default)"
    if rc != 0:
        return GateResult(
            PESSIMISM_SKILL, SKIP,
            f"skill dispatch failed (exit {rc}): {err or 'no stderr'}",
            model=model, output=out,
        )

    verdict = _last_verdict(out, "PESSIMISM-VERDICT:")
    if verdict == "CLEAN":
        return GateResult(PESSIMISM_SKILL, PASS,
                          "no unsupported completion claims flagged", model=model, output=out)
    if verdict == "FLAGGED":
        return GateResult(PESSIMISM_SKILL, FAIL,
                          "pessimism flagged unsupported completion claim(s)", model=model, output=out)
    # No explicit verdict line — fall back to conservative keyword scan; never auto-pass.
    if _looks_flagged(out):
        return GateResult(PESSIMISM_SKILL, FAIL,
                          "no verdict line; output reads as flagged (conservative FAIL)",
                          model=model, output=out)
    return GateResult(PESSIMISM_SKILL, SKIP,
                      "skill returned no parseable verdict (not asserting PASS)",
                      model=model, output=out)


def run_judge_gate() -> GateResult:
    ready, reason = preflight()
    if not ready:
        return GateResult(JUDGE_SKILL, SKIP, f"harness unavailable: {reason}")
    if _model_is_ollama() and not _ollama_reachable():
        return GateResult(
            JUDGE_SKILL, SKIP,
            "Ollama not reachable (local critic model) — start `ollama serve` or set SUBMISSION_MODEL",
        )

    rc, out, err = invoke_skill(JUDGE_SKILL, build_deliverable_summary())
    model = resolve_model() or "(skill/global default)"
    if rc != 0:
        return GateResult(
            JUDGE_SKILL, SKIP,
            f"skill dispatch failed (exit {rc}): {err or 'no stderr'}",
            model=model, output=out,
        )

    verdict = _last_verdict(out, "JUDGE-VERDICT:")
    if verdict == "PASS":
        return GateResult(JUDGE_SKILL, PASS, "judge panel returned a passing verdict",
                          model=model, output=out)
    if verdict == "FAIL":
        return GateResult(JUDGE_SKILL, FAIL, "judge panel verdict is not passing",
                          model=model, output=out)
    return GateResult(JUDGE_SKILL, SKIP,
                      "judge panel returned no parseable verdict (not asserting PASS)",
                      model=model, output=out)


# ---------------------------------------------------------------------------
# Verdict parsing helpers
# ---------------------------------------------------------------------------


def _last_verdict(output: str, marker: str) -> str | None:
    """Return the token after the LAST line containing `marker` (case-insensitive),
    uppercased. None if absent."""
    found: str | None = None
    for line in output.splitlines():
        idx = line.upper().find(marker.upper())
        if idx != -1:
            tail = line[idx + len(marker):].strip().strip(".").upper()
            token = tail.split()[0] if tail else ""
            if token:
                found = token
    return found


def _looks_flagged(output: str) -> bool:
    low = output.lower()
    flagged = any(w in low for w in ("unsupported", "flagged", "no evidence", "hand-wav", "not verified"))
    clean = any(w in low for w in ("no unsupported", "all claims", "clean", "every claim has"))
    return flagged and not clean


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_ICON = {PASS: "[PASS]", FAIL: "[FAIL]", SKIP: "[SKIP]"}


def print_report(results: list[GateResult], *, verbose: bool) -> None:
    print("\n" + "=" * 70)
    print("AI SHOWRUNNER — SUBMISSION GATE  (PRD §10 / bead asr-av5.6)")
    print("=" * 70)
    for r in results:
        print(f"\n{_ICON[r.status]}  {r.name}")
        print(f"        {r.detail}")
        if r.model:
            print(f"        model: {r.model}")
        if verbose and r.output:
            print("        ---- skill output ----")
            for line in r.output.splitlines():
                print(f"        | {line}")
    print("\n" + "-" * 70)


def overall_exit(results: list[GateResult], *, strict: bool) -> int:
    if any(r.status == FAIL for r in results):
        return 1
    if strict and any(r.status == SKIP for r in results):
        return 1
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="AI Showrunner submission gate (asr-av5.6).")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--pessimism-only", action="store_true", help="run only the pessimism gate")
    g.add_argument("--judge-only", action="store_true", help="run only the judge-panel gate")
    p.add_argument("--strict", action="store_true", help="treat SKIP as failure (exit 1)")
    p.add_argument("-v", "--verbose", action="store_true", help="print full skill output")
    args = p.parse_args(argv)

    ready, reason = preflight()
    if not ready:
        print(f"[warn] harness substrate unavailable: {reason}")
        print("[warn] gates will SKIP (not PASS). This run is safe but non-authoritative.")

    results: list[GateResult] = []
    if not args.judge_only:
        results.append(run_pessimism_gate())
    if not args.pessimism_only:
        results.append(run_judge_gate())

    print_report(results, verbose=args.verbose)

    code = overall_exit(results, strict=args.strict)
    summary = "READY (all run gates passed)" if code == 0 else "NOT READY"
    if any(r.status == SKIP for r in results) and code == 0:
        summary += " — note: one or more gates SKIPPED; re-run with the harness up before submitting"
    print(f"OVERALL: {summary}  (exit {code})")
    print("-" * 70)
    return code


if __name__ == "__main__":
    sys.exit(main())
