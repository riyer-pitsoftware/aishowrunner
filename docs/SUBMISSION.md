# AI Showrunner — Submission Checklist (PRD §10)

Qwen Cloud Hackathon · **Track 2 — AI Showrunner** · **Deadline: 2026-07-09 @ 2:00 pm PDT**

This document maps every hackathon hard requirement to evidence in the repo, and
defines the two submission gates that must pass before we ship. Source of truth
for requirements + weights: `memory/hackathon-facts`. Source of truth for
acceptance evidence: `docs/uat/suites/` (per-sprint UAT-7 + submission UAT-6).

---

## Judging weights (AUTHORITATIVE — overrides team-judge-panel defaults)

| Axis                              | Weight |
|-----------------------------------|:------:|
| Technical Depth & Engineering     |  30%   |
| Innovation & AI Creativity        |  30%   |
| Problem Value & Impact            |  25%   |
| Presentation & Documentation      |  15%   |

These weights are encoded into the judge-panel gate prompt in
`scripts/submission_gate.py` (`build_deliverable_summary`).

---

## The two submission gates

PRD §10 gates the submission on **(a)** a passing judge-panel verdict and **(b)**
a pessimism review that finds no unsupported completion claims. Both run through
`scripts/submission_gate.py`, which invokes the real skills via the agentic-harness
runtime (`runtime/run_skill.py`) — the same mechanism the product's
`SubprocessSkillPort` uses — and **never fabricates a PASS**.

```bash
python scripts/submission_gate.py            # both gates
python scripts/submission_gate.py --pessimism-only
python scripts/submission_gate.py --judge-only
python scripts/submission_gate.py --strict   # treat SKIP as failure
python scripts/submission_gate.py -v         # print full skill output
```

### Gate A — Pessimism (no unsupported completion claims)
- **Skill:** `pessimism` (`backend/showrunner_skills/pessimism/`, kept verbatim).
- **Reviews:** the completion claims assembled from `docs/uat/suites/UAT-7-sprint-acceptance.md`
  + `git log` + closed beads (`bd list --status closed`).
- **Passes when** the skill emits `PESSIMISM-VERDICT: CLEAN`. **Fails** on `FLAGGED`.
  No parseable verdict ⇒ SKIP (conservative; never auto-PASS).

### Gate B — Judge Panel (passing rubric verdict)
- **Skill:** `team-judge-panel` (`backend/showrunner_skills/team-judge-panel/`, verbatim).
- **Reviews:** the deliverable summary (what the product does) against the
  authoritative rubric weights above.
- **Passes when** the panel emits `JUDGE-VERDICT: PASS`. **Fails** on `FAIL`.

### Behaviour by environment
- **Harness + Ollama (or Qwen Cloud) available:** the gate shells out to
  `run_skill.py`, resolves the `critic` tier from `.harness/models.yaml`, pipes
  the claims/summary on stdin, and reports a real PASS/FAIL from the model verdict.
- **Harness / `uv` / Ollama unavailable:** the gate reports **SKIP** with a clear
  warning — it does not crash and it does not assert PASS. Overall exit stays 0
  (so it is safe to run anywhere) unless `--strict` is passed, which turns any
  SKIP into exit 1. Use `--strict` for the authoritative pre-submission run.

### Configuration (env overrides defaults from repo settings)

| Var                 | Default                            | Purpose                                   |
|---------------------|------------------------------------|-------------------------------------------|
| `HARNESS_REPO`      | `~/code/agentic-harness`           | location of `runtime/run_skill.py`        |
| `SHOWRUNNER_MODELS` | `<repo>/.harness/models.yaml`      | model tier map                            |
| `SUBMISSION_MODEL`  | (unset)                            | explicit `PROVIDER/MODEL` override        |
| `SKILL_PORT`        | `subprocess`                       | informational (gate uses subprocess port) |
| `SKILL_TIMEOUT_S`   | `180`                              | per-skill timeout                         |
| `OLLAMA_BASE_URL`   | `http://localhost:11434`           | local model reachability probe            |

For the authoritative cloud run, repoint the `critic` tier in
`.harness/models.yaml` to `qwen-cloud/qwen-plus` (the local coder model follows
critic structure without real skepticism — see the CRITIC CAVEAT in that file),
or set `SUBMISSION_MODEL=qwen-cloud/qwen-plus`.

---

## Hard requirement → evidence map

| # | Hard requirement (memory/hackathon-facts) | Evidence in repo | UAT | Bead / commit |
|---|---|---|---|---|
| 1 | **Qwen models on Qwen Cloud** (load-bearing) | `backend/.../showrunner/skills/` (Skill Plane → Qwen via harness); `.harness/models.yaml` cloud tiers; media via Alibaba Wan/CosyVoice | UAT-SUB-001, UAT-SKILL-006 | `asr-av5.1` (cloud wiring) · `f916acb` |
| 2 | **Public OSS repo + detectable license** | `LICENSE`, `README.md`, commit history after 2026-05-26 | UAT-SUB-002 | repo (Sprints 1+) |
| 3 | **Proof of Alibaba Cloud deployment** | deployed URL + console screenshot | UAT-SUB-003 | `asr-av5.3` (open) |
| 4 | **Architecture diagram** | 3-layer diagram (UI / orchestration: Skill+Media planes / data) | UAT-SUB-007 | docs |
| 5 | **Demo video ~3 min** (YouTube/Vimeo/Facebook) | hosted video URL + duration | UAT-SUB-004 | `asr-av5.5` (open) |
| 6 | **Track identified (AI Showrunner)** | README + Devpost declare Track 2 | UAT-SUB-008 | docs |
| — | **Judge Panel passing verdict** | Gate B output artifact | UAT-SUB-005 | `asr-av5.6` — this gate |
| — | **Pessimism review clean** | Gate A output artifact | UAT-SUB-006 | `asr-av5.6` — this gate |

Per-sprint build evidence (the base for Gate A) lives in
`docs/uat/suites/UAT-7-sprint-acceptance.md`: S1 `asr-497` · S2 `asr-0bj` ·
S3 `asr-63f` · Cost `asr-3mk` · S4 `asr-n88` · S5 `asr-0ei` · S6 `asr-2in` ·
S7 `asr-av5`.

---

## Ready-to-submit checklist

A box is checked **only** when its evidence is verifiable today.

- [ ] **1. Qwen Cloud load-bearing & visible in audit** — UAT-SUB-001 passes in CLOUD
- [ ] **2. Public OSS repo + license** — UAT-SUB-002
- [ ] **3. Alibaba Cloud deployment proof** — UAT-SUB-003 (`asr-av5.3` open)
- [ ] **4. Architecture diagram present** — UAT-SUB-007
- [ ] **5. Demo video ≤ ~3 min hosted** — UAT-SUB-004 (`asr-av5.5` open)
- [ ] **6. Track identified (AI Showrunner)** — UAT-SUB-008
- [ ] **7. Gate A — pessimism CLEAN** — `python scripts/submission_gate.py --pessimism-only --strict` exits 0
- [ ] **8. Gate B — judge-panel PASS** — `python scripts/submission_gate.py --judge-only --strict` exits 0

**READY TO SUBMIT = all 8 boxes checked AND
`python scripts/submission_gate.py --strict` exits 0.**

> Current status: NOT READY. Sprint 7 deployment/demo beads (`asr-av5.3`,
> `asr-av5.5`) are open, and the gates must be run with the harness up (Qwen) on
> the final claim set. The gate is wired and runnable now (it really invokes the
> skills — no hardcoded PASS); the checklist closes as the remaining hard
> requirements land.
