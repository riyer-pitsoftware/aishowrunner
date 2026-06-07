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

### UAT-S4 — Sprint 4: Showrunner Rooms & Gates  ☐ (executes UAT-2; UAT-PROD-002/003/008)
### UAT-S5 — Sprint 5: Episode Room UI  ☐ (executes UAT-4)
### UAT-S6 — Sprint 6: Media Production  ☐ (executes UAT-PROD-005/006/007; UAT-COST-002)
### UAT-S7 — Sprint 7: Cloud & Submission  ☐ (executes UAT-6; UAT-SKILL-006; UAT-SUB-*)
