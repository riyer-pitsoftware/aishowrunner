# AI Showrunner — User Acceptance Testing (UAT)

This is the acceptance evidence pack for the AI Showrunner (Qwen Cloud Hackathon,
Track 2). It defines **how the output is tested** — by a human acceptance tester,
end to end — and maps every test back to the PRD acceptance criteria (PRD §10) and
the hackathon's hard requirements (`memory/hackathon-facts`, mirrored in
[UAT-MASTER-PLAN](UAT-MASTER-PLAN.md)).

> UAT answers one question per case: *would the user/judge accept this?* — not
> *does the unit test pass?* Unit/integration tests live in `backend/tests/`;
> UAT is black-box, user-facing, evidence-backed.

## Documents

| File | Purpose |
|---|---|
| [UAT-MASTER-PLAN.md](UAT-MASTER-PLAN.md) | Scope, traceability matrix, entry/exit criteria, sign-off |
| [suites/UAT-1-skill-system.md](suites/UAT-1-skill-system.md) | Skills loaded from forks, Qwen routing, authorship, no monolith |
| [suites/UAT-2-team-workflow.md](suites/UAT-2-team-workflow.md) | Rooms convene, gates block, disagreements stay visible |
| [suites/UAT-3-product-workflow.md](suites/UAT-3-product-workflow.md) | Full create→produce→choose→canon loop |
| [suites/UAT-4-ui.md](suites/UAT-4-ui.md) | Episode Room legibility, 9:16 stage, artifacts |
| [suites/UAT-5-cost-budgeting.md](suites/UAT-5-cost-budgeting.md) | Metering, pricing, reserve→commit, budget blocks |
| [suites/UAT-6-submission.md](suites/UAT-6-submission.md) | Qwen Cloud load-bearing, Alibaba deploy, demo, OSS repo |
| [suites/UAT-7-sprint-acceptance.md](suites/UAT-7-sprint-acceptance.md) | Per-sprint developer-acceptance gates (executable now) |

## Environments

| Env | Skill model | Media | DB | Purpose |
|---|---|---|---|---|
| **LOCAL** | Qwen via Ollama (`.harness/models.yaml`) | n/a or stub | Postgres (docker) | day-to-day UAT |
| **CLOUD** | Qwen Cloud (DashScope) | Alibaba Wan + CosyVoice | managed PG | submission UAT |

Prereqs (LOCAL): Docker, Ollama running with a Qwen model
(`ollama pull qwen2.5-coder:14b`), `cp .env.example .env`, `docker compose -f
docker-compose.dev.yml up`, `alembic upgrade head`.

## Test case format

Each case is a table:

- **ID** — `UAT-<AREA>-<NNN>` (stable; referenced by the traceability matrix)
- **Maps to** — PRD §10 criterion and/or hackathon requirement
- **Priority** — P0 (submission-blocking) · P1 · P2
- **Preconditions**, **Steps**, **Test data**, **Expected result**
- **Result** — Pass / Fail / Blocked / N-A (filled at execution)
- **Evidence** — screenshot file, response capture, audit-trace export, or log line

## Status legend

`☐ not run` · `☑ pass` · `✗ fail` · `▣ blocked` · `– n/a`

## Execution & evidence

1. Pick a suite, execute cases top-to-bottom on the target env.
2. Record Result + Evidence inline (commit evidence under `docs/uat/evidence/<date>/`).
3. Roll the suite result up into the master plan sign-off table.
4. A release is **acceptance-complete** when every **P0** case is `pass` on CLOUD
   and the master plan is signed off.
