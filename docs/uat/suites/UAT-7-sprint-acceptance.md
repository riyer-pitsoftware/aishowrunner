# UAT Suite 7 — Per-Sprint Acceptance Gates

Developer-acceptance gates run at the end of each build sprint (TRD §15). These are
executable now and verify the build increments. Sprints 1–3 are complete and
verified; 4–7 are defined ahead of time.

Commands assume repo root unless noted; the showrunner test subset runs without
the full backend env:
```bash
uv venv /tmp/sr-venv && uv pip install --python /tmp/sr-venv/bin/python \
  pytest pytest-asyncio pyyaml sqlalchemy pgvector
cd backend && PYTHONPATH=src /tmp/sr-venv/bin/python -m pytest tests/showrunner -q
```

---

### UAT-S1 — Sprint 1: Harness & Foundation  ☑ PASS (2026-06-06)
- `~/code/agentic-harness/bin/harness-init … --dry-run` → scaffolds `.planning/build/`. **Observed:** STATUS/ROSTER/AGENTIC-HARNESS created.
- Project `.harness/models.yaml` resolves Qwen tiers. **Observed:** `run_skill.py pessimism` → `model: ollama/qwen2.5-coder:14b`.
- Lightweight ChronoCanvas fork. **Observed:** source/config present; `output/`, `.git`, `.env`, `.beads` absent.
- 13 forks in `backend/showrunner_skills/`; 12 role memories + ROSTER. **Observed:** counts verified; deadline 2026-07-09 in `pm.md`.
- **Gate:** pessimism review + verification → closed `asr-497`.

### UAT-S2 — Sprint 2: Skill Runtime & Bridge  ☑ PASS (2026-06-06)
- `pytest tests/showrunner/test_skill_runtime.py` → unit logic green.
- Real end-to-end: `pytest tests/showrunner/test_skill_smoke.py` → pessimism through `run_skill.py` → Qwen on Ollama. **Observed:** `status ok`, model contains `qwen`.
- `GET /api/skills` / `/{name}` serve forks with content hash.
- **Observed:** `30 passed` (cumulative), ruff clean. **Gate:** pessimism → closed `asr-0bj`.

### UAT-S3 — Sprint 3: Series Brain (Canon)  ☑ PASS (2026-06-07)
- Models registered: `pytest -k test_all_showrunner_tables_registered` → 16 tables in metadata.
- Canon fold correctness: add/update/retire facts, threads open/resolve, order-independence, unknown-type skip, provenance. **Observed:** `test_canon.py` fold cases green.
- Immutability: `_block_update`/`_block_delete` raise; selected choice frozen; guards register idempotently. **Observed:** green.
- State machine: full happy path + reconsider/revise loops + invalid-transition raise + `next_required_gate`. **Observed:** green.
- Series API (executable): `POST/GET /api/series`, `GET /api/series/{id}/canon` (fold). **Observed:** 30 → with Sprint 3 suite, **30 passed** total in `tests/showrunner`, ruff clean, migration `010` compiles.
- **Gate:** pessimism → close `asr-63f`.

> DB-integration note: `skill_invocations` + Series Brain tables use Postgres
> types (UUID/JSONB/ARRAY). Migration `010` is verified by compile + metadata
> registration; full `alembic upgrade head` runs against Postgres in LOCAL/CLOUD
> (a containerized PG integration test is tracked for the Rooms sprint).

---

### UAT-S4 — Sprint 4: Showrunner Rooms & Gates  ◑ CODE COMPLETE / live-run pending
- Deterministic cores unit-tested (16 tests): disagreement comparator (stance + block + historian field-conflict, no false consensus), gate mapping `gate_target`, `idempotent_transition`, room rosters = exact PRD skills, `build_requests`, briefing format, event payloads.
- Services: `RoomService` (fan-out → persist invocation+contribution → comparator → events), `GateService` (immutable ApprovalGate + frozen dissent snapshot + state advance), `EpisodeService` (create + idempotent advance).
- API live: `POST /series/{id}/story-room`, `/episodes/{id}/production-desk` (background jobs), `GET /episodes/{id}`, `/contributions`, `/disagreements`, `POST /greenlights/{gate}` (budget reserve at episode gate → `409 budget_exceeded`).
- **Observed:** 60 tests pass (showrunner suite); ruff clean. **Gate:** pessimism → closed `asr-n88`.
- **PENDING live-run (asr-05c, needs DB+Ollama):** UAT-2 (all), UAT-PROD-002/003/008. Background jobs use FastAPI BackgroundTasks (ARQ offload is a later enhancement).
### UAT-S5 — Sprint 5: Episode Room UI  ◑ CODE COMPLETE / in-browser verify pending
- Shared frontend foundation: `api/showrunner/types.ts` (mirrors backend schemas), `api/showrunner/hooks.ts` (React Query hooks for series/canon/episode/rooms/greenlight/budget/cost), `components/showrunner/stance.ts`.
- Three-room shell `pages/EpisodeRoom.tsx` (asr-0ei.1): one room active/expanded, others compact/clickable; follows episode lifecycle until a room is pinned. Route `/room?series=&episode=` wired in `App.tsx`; sidebar "Episode Room" item added (default + hackathon nav).
- Persistent 9:16 stage `Stage916.tsx` (asr-0ei.5): right rail across all rooms; status placeholder until media lands (Sprint 6).
- Story Room (asr-0ei.2/.6): `StoryRoomPanel` (convene → navigate; CanonRail + contribution feed), `ContributionCard` (authorship + stance + progressive disclosure), `CanonRail`, `BranchProposals` (forward-compatible).
- Production Desk (asr-0ei.3/.7): `ProductionDeskPanel`, `BudgetBar` (stacked spent/reserved vs limit + soft-cap marker), `CostPanel` (rollup + invocation table + pre-flight estimate w/ outcome), `ShotTimeline` (production-desk contributions; shot strip stubbed for Sprint 6).
- Greenlight (asr-0ei.4): `GreenlightPanel` (status + derived gate + council roster), `VerdictControls` (per-gate verdicts, episode-gate estimate_usd, 409 budget_exceeded callout), `DisagreementList` (verbatim per-skill stances — dissent preserved, UAT-TEAM-004/005).
- **Built via shared foundation (inline) + 3 parallel agents on disjoint panel files.** Panels typed against the foundation; signatures verified against the shell by inspection. **No `node_modules` in the lite fork → `tsc`/`vite build` not run here.**
- **PENDING in-browser verify (executes UAT-4):** `npm i && npm run dev` against a live backend (DB+Ollama, asr-05c); walk the three rooms, convene, greenlight, budget surfaces, 9:16 stage.
### UAT-S6 — Sprint 6: Media Production  ☐ (executes UAT-PROD-005/006/007; UAT-COST-002)
### UAT-S7 — Sprint 7: Cloud & Submission  ☐ (executes UAT-6; UAT-SKILL-006; UAT-SUB-*)
