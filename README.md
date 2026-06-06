# AI Showrunner

**Qwen Cloud Hackathon — Track 2 (AI Showrunner).** An AI show runner inspired by ChronoCanvas.

> Assemble a showrunner team, give it a series premise, and repeatedly produce
> audience-steered 60–90s vertical **historical-noir** episodes that preserve
> canon and improve through specialist review.

AI Showrunner is a persistent production workspace, not a chatbot. It is operated
by visible showrunner *teams* composed exclusively from existing Claude `team-*`
skills — the **same skills** are used both to *build* the app (via agentic-harness
Layer B + Beads) and to *run* it inside the shipped product. **Qwen supplies the
model intelligence** (Qwen via Ollama locally, **Qwen Cloud** in deployment) —
Qwen is the runtime, never the role definition.

## Showrunner rooms

| Room | Skills | Owns |
|---|---|---|
| **Story Room** | creative-director, narrative-engineer, historian, game-designer | premise, beats, branches, audience choices, accuracy classes |
| **Production Desk** | line-producer, ml-engineer, cloud-economist, frontend, backend, devops | shot plan + dependency graph, media routing, **cost envelope**, assembly |
| **Greenlight Council** | pm, judge-panel, pessimism | Branch / Episode / Final-Cut approval gates |

Specialist disagreements stay **visible** — the system never synthesizes false consensus.

## Architecture

```
Episode Room UI (React/TS · Tailwind · Zustand · XYFlow)
        │ REST + Redis pub/sub
Product Orchestration (FastAPI · chronocanvas.showrunner.*)
   ├── Skill Plane  → agentic-harness Layer B (single-skill) → Qwen (Ollama / Qwen Cloud)
   ├── Media Plane  → LangGraph pipeline → Alibaba Wan (image/video) + CosyVoice (TTS)
   ├── Series Brain → append-only canon w/ provenance
   └── Cost & Budgeting → priced ledger + reserve→commit enforcement
Postgres (canon · episodes · invocations · budgets) · Redis (ARQ + pub/sub)
```

- **Qwen Cloud is load-bearing and visible in audit traces** (`/api/episodes/{id}/audit`).
- **agentic-harness Layer B stays narrow** — single-skill invocation only;
  orchestration lives in the product.
- **Cost & budgeting is first-class**: every skill call and media job is metered,
  priced, attributed to series/episode/decision, and checked against a budget
  *before* expensive work runs.

Built on a lightweight fork of **ChronoCanvas** (React/TS/Vite + FastAPI/async
SQLAlchemy/Postgres/Redis/ARQ/LangGraph).

## Documentation

- [`PRD.md`](PRD.md) — product requirements (executable PRD).
- [`docs/TRD.md`](docs/TRD.md) — technical design: harness bridge, cost/budgeting, rooms, canon.
- [`docs/reference/`](docs/reference/) — upstream ChronoCanvas docs (provenance).

## Local development

Requires Docker + [Ollama](https://ollama.com) with a Qwen model pulled
(`ollama pull qwen2.5-coder:14b`). Skill routing is configured in
`.harness/models.yaml`; media/cloud routing switches to Qwen Cloud + Alibaba in
deployment.

```bash
cp .env.example .env        # fill secrets
docker compose -f docker-compose.dev.yml up
```

## Status

Built sprint-by-sprint via agentic-harness with Beads issue tracking (prefix
`asr-`). Sprint 1 (harness, fork, skill onboarding, Qwen/Ollama routing) complete;
see `docs/TRD.md` §15 for the sprint plan.

## License

See [`LICENSE`](LICENSE).
