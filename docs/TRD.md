# AI Showrunner — Technical Requirements Document (TRD)

Companion to `PRD.md` (executable PRD target: `docs/PRD.md`).

| | |
|---|---|
| **Build workspace** | `/Users/riyer/code/qwencloud-aishowrunner` |
| **Foundation (fork)** | `/Users/riyer/code/chrono-canvas` |
| **Execution substrate** | `/Users/riyer/code/agentic-harness` (Layer B) |
| **Model runtime** | Qwen via Ollama (local) / Qwen Cloud (deploy) |
| **Status** | Draft v1 — derived from PRD + codegraph analysis of both source repos |

This TRD turns the PRD into an implementable design. Two requirements drive every
decision below:

1. **Agentic-harness is the only skill-execution substrate.** The product never
   re-implements model dispatch for *skills*. It calls harness Layer B
   (`run_skill.py` / `HarnessAgent`) and stays an orchestrator on top. Harness
   Layer B must remain narrow (single-skill invocation) — orchestration lives in
   the product, never pushed down into the harness.
2. **Cost and budgeting are first-class.** Every skill invocation and every media
   generation is metered, priced, attributed to a series/episode/decision, and
   checked against a budget *before* expensive work runs. team-cloud-economist
   (Fin) is backed by a real subsystem, not a prompt.

---

## 1. Gap Analysis (PRD → TRD)

The PRD is strong on product behavior and constraints but leaves the following
engineering decisions unspecified. Each is resolved in this TRD.

| # | Gap in PRD | Resolution (section) |
|---|---|---|
| G1 | **Sync→async bridge.** `HarnessAgent` is synchronous (Pydantic AI); FastAPI/ARQ are async. No stated mechanism to call skills from the backend. | §4 Skill Runtime Bridge — invoke in ARQ worker via threadpool/subprocess; never block the event loop. |
| G2 | **Structured contributions.** Skills return free text (`AgentResult.content`), but the UI needs typed artifacts (cost envelope, consequence map). No contract. | §5 Skill Contribution Contract — envelope prompt + JSON schema + tolerant parser + raw-text fallback. |
| G3 | **Disagreement detection.** PRD requires visible disagreements but skills run independently. No algorithm. | §8.4 Disagreement Detection — structured stance fields + deterministic comparator, no LLM "consensus" step. |
| G4 | **Two routing planes.** Harness `models.yaml` routes *skill text*; chrono-canvas `LLMRouter` routes *media/generation*. PRD conflates them. | §7 Model Routing — explicit split: Skill Plane (harness) vs Media Plane (chrono-canvas). |
| G5 | **Cost derivation.** Ollama returns `cost=0.0`; harness logs tokens to a JSONL ledger, not the DB. No pricing table, no unified ledger, no $ for Qwen Cloud. | §6 Cost & Budgeting — pricing table, unified `SkillInvocation` ledger in Postgres, cost = tokens × price. |
| G6 | **Budget enforcement.** "Estimate and monitor budget" is named but no caps, pre-flight estimate, or block behavior. | §6.4–6.6 — per-series/per-episode budgets, pre-flight estimate at Episode Greenlight, hard/soft caps, enforcement at `produce`. |
| G7 | **Approval-gate state machine.** Three gates listed; no episode lifecycle/state transitions/idempotency. | §8.2 Episode State Machine. |
| G8 | **Selective regeneration.** "Dependency-aware" regeneration named; no dependency model or invalidation rule. | §9 Media Production & Selective Regeneration. |
| G9 | **Canon provenance/immutability.** "Cannot be silently rewritten" stated; no enforcement mechanism. | §10 Canon Model — append-only mutations + provenance FK + no in-place UPDATE. |
| G10 | **Qwen model identifiers.** PRD says "verify exact Qwen identifiers during implementation." | §7.3 — resolution checklist + `models.yaml` + pricing table are the single source of truth. |
| G11 | **Skill versioning/audit.** PRD wants skill version/content hash recorded; no scheme. | §5.4 — SHA-256 of resolved `SKILL.md` stored per invocation. |
| G12 | **Continuity evaluation.** team-ml-engineer "validates continuity-evaluation workflows"; undefined. | §9.4 — optional critic-tier eval pass, behind a budget flag. |

---

## 2. System Context & Layering

```
┌──────────────────────────────────────────────────────────────────────┐
│ Episode Room UI  (React/TS/Vite/Tailwind/Zustand/React Query/XYFlow)   │
│  Story Room · Production Desk · Greenlight Council · 9:16 preview       │
└───────────────▲───────────────────────────────────────────────────────┘
                │ REST + Redis pub/sub (SSE/WS)
┌───────────────┴───────────────────────────────────────────────────────┐
│ PRODUCT ORCHESTRATION  (new, in chrono-canvas fork, FastAPI)           │
│  Room services · Approval gates · Disagreement engine · Canon brain    │
│  Budget engine · Selective-regen planner                               │
│        │                                   │                            │
│        │ skill calls                       │ media calls                │
│        ▼                                   ▼                            │
│ ┌──────────────────────────┐   ┌────────────────────────────────────┐ │
│ │ SKILL PLANE              │   │ MEDIA PLANE                        │ │
│ │ agentic-harness Layer B  │   │ chrono-canvas LLMRouter +          │ │
│ │ HarnessAgent/run_skill   │   │ image/video/TTS providers          │ │
│ │ .harness/models.yaml     │   │ LangGraph pipeline + ARQ           │ │
│ │ → Qwen (Ollama/Cloud)    │   │ → Qwen Cloud / media providers     │ │
│ └──────────────────────────┘   └────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
        │ persistence
┌───────┴────────────────────────────────────────────────────────────────┐
│ Postgres (canon, episodes, invocations, budgets) · Redis (ARQ + pubsub) │
└──────────────────────────────────────────────────────────────────────────┘
```

**Invariant:** the Product Orchestration layer is the *only* place that knows how
to run a "room." It composes many single-skill calls. It must not be moved into
the harness, and the harness must not gain pipeline/sub-agent features (PRD §7.1,
MVP exclusion: "Replacing agentic-harness with a custom multi-agent framework").

---

## 3. Technology Baseline (inherited from chrono-canvas)

Retained as-is (PRD §7.3): React/TS/Vite/Tailwind/Zustand/React Query/XYFlow;
FastAPI, async SQLAlchemy, PostgreSQL, Redis, ARQ, LangGraph; `OllamaProvider`;
existing story/scene/narration/assembly pipeline, `ProgressPublisher` (Redis
pub/sub), audit middleware, `CostTracker`, `LLMRouter` fallback chain, ConfigHUD
`RuntimeConfig`.

New Python package namespace: `chronocanvas.showrunner.*` (rooms, skills, canon,
budget). Reusing existing `chronocanvas.llm.*`, `chronocanvas.services.progress`,
`chronocanvas.db.*`.

---

## 4. Skill Runtime Bridge (agentic-harness integration)

### 4.1 Invocation path

The product calls skills through a single internal port:

```python
# chronocanvas/showrunner/skills/port.py
class SkillPort(Protocol):
    async def invoke(self, req: SkillCallRequest) -> SkillCallResult: ...
```

`SkillCallRequest`:

| field | source |
|---|---|
| `skill_name` | e.g. `team-historian` (must exist on disk; §5.1) |
| `message` | composed by the room service (canon briefing + task) |
| `model_tier` override (optional) | maps to `models.yaml` tier |
| `model` override (optional) | exact `provider/model` for pinning/eval |
| `series_id`, `episode_id`, `decision_id` | attribution for cost ledger |
| `budget_token` | reservation handle from the budget engine (§6.5) |

### 4.2 Implementation — `HarnessAgentSkillPort`

Primary adapter wraps `runtime/agent.py::HarnessAgent`:

- Construct `HarnessAgent(skill_name=..., memory_dir=<project .planning>)`. This
  reuses the harness `MemoryEnvelope` (ROSTER.md / STATUS.md lede / per-role
  memory at `~/.claude/projects/-Users-...-aishowrunner/memory/team/<role>.md`).
  **Project-specific behavior stays in role memory, never in app code** (PRD §3).
- `HarnessAgent.run()` is **synchronous** → call it via
  `anyio.to_thread.run_sync(...)` so the FastAPI event loop is never blocked.
- Heavy/parallel room fan-out runs inside an **ARQ worker job**, not the request
  handler. The HTTP `POST /story-room` returns immediately with an `episode_id`
  and streams progress via Redis (§12).

**Fallback adapter — `SubprocessSkillPort`** shells out to
`agentic-harness/runtime/run_skill.py <skill> --model <m> --message -` over
stdin/stdout. Used when (a) a skill needs hard process isolation, or (b)
`HarnessAgent`'s Pydantic-AI provider mapping doesn't yet cover the configured
Qwen Cloud endpoint. The port abstraction lets us switch per-skill without
touching room logic. Selection via `SHOWRUNNER_SKILL_PORT={inprocess|subprocess}`.

### 4.3 What the harness must NOT do

No changes to harness Layer B beyond what `harness-init` produces. No multi-skill
loop, no sub-agent dispatch added to `agent.py`. If the harness lacks a Qwen Cloud
provider mapping, we add it via `models.yaml` + LiteLLM/Pydantic-AI provider
config (an `ollama`-compatible or OpenAI-compatible base URL), **not** by adding
orchestration code.

### 4.4 Concurrency & resilience

- Room fan-out = bounded `asyncio.gather` over threadpool calls; concurrency
  capped by `SHOWRUNNER_SKILL_MAX_CONCURRENT` (default 3) to bound local Ollama /
  Qwen Cloud RPM. Reuse chrono-canvas `RateLimiter` semantics where convenient.
- Per-skill timeout (default 120 s, matching `OllamaProvider`'s httpx timeout).
- Retries: 1 retry on dispatch failure (harness exit code 2 / transport error),
  exponential backoff. Persistent failure → contribution recorded with
  `status=failed`, surfaced in the room (PRD: no indefinite spinners).

---

## 5. Skill Discovery & Contribution Contract

### 5.1 Discovery & loading (PRD §3, §7.1)

- Canonical skills: `~/.claude/skills/<name>/SKILL.md`.
- Project forks (authoritative for the product): `.claude/skills/<name>/SKILL.md`,
  installed via `team-onboard`. The harness `find_skill` order already prefers
  `~/.claude/skills`; the product must additionally honor the **project-local
  fork** — so the registry resolves project `.claude/skills` *first*, then falls
  back to the harness search path.
- `GET /api/skills` and `GET /api/skills/{name}` read the resolved file; they
  return name, description, role summary, source path, and `content_hash`. Skill
  prompt text is **never** duplicated into app source (acceptance test: "loaded
  without rewriting their role definitions").

### 5.2 Registry table — `skill` (cache, not source of truth)

`name, source_path, content_hash (sha256), description, default_tier,
last_loaded_at`. Rebuilt on startup and on demand; the file on disk always wins.

### 5.3 Structured output (resolves G2)

Skills emit prose by default. To render production artifacts we wrap the room's
task message with a **contribution envelope** appended to the skill's own
instructions (not replacing them):

```
<task>...room-specific request...</task>
Return your specialist judgment as prose, then a single fenced ```json block
matching this contract: { "summary": str, "stance": "support"|"concern"|"block",
"recommendations": [str], "risks": [str], "fields": { ... role-specific ... } }
```

A **tolerant parser** extracts the last fenced `json` block; on parse failure the
contribution is stored as `raw_text` with `structured=null` and still displayed
(progressive disclosure shows raw output anyway). Role-specific `fields` are
documented per skill (e.g. Fin → `{est_cost_usd, cost_drivers[], budget_risk}`;
game-designer → `{choices[], consequences[]}`).

> Rationale: keeps skill SKILL.md untouched (PRD §3) while giving the UI typed
> data. The envelope is product orchestration, allowed by §7.1.

### 5.4 Invocation record (PRD §7.1, resolves G11)

Every call writes a `skill_invocation` row (§6.3) capturing: skill name,
`content_hash`, resolved model, input/output/cached tokens, duration, series,
episode, decision, resulting artifact id, provider, and computed cost.

---

## 6. Cost & Budgeting Subsystem  ★ (primary emphasis)

Unifies harness token accounting and chrono-canvas `CostTracker` into one priced,
attributed, enforceable ledger.

### 6.1 Sources of usage

| Plane | Usage source | Cost at source |
|---|---|---|
| Skill (harness) | `AgentResult` / `run_skill` stdout; tokens from harness or recomputed | unpriced (tokens only) |
| Skill (harness, build-time) | `.beads/token-ledger.jsonl` `{input,output,cached,total}` | unpriced |
| Media (chrono-canvas) | `LLMResponse.{input_tokens,output_tokens,cost}` | Ollama=0.0; cloud providers price themselves |

Problem: harness `HarnessAgent.AgentResult` exposes `{content, model, skill}` but
**not** token counts. Mitigations, in priority order:
1. Prefer the `SubprocessSkillPort` + `run_skill.py` path when token capture is
   required and harness stdout/`_log_usage` exposes counts; parse the ledger entry.
2. If counts are unavailable, **estimate** tokens with a tokenizer
   (`tiktoken`/`qwen` BPE approximation) over the rendered prompt + response and
   mark `tokens_estimated=true`.
3. Track upstream issue to add token usage to `AgentResult` (out of scope to
   modify the harness here; estimation is the contract).

### 6.2 Pricing table (resolves G5/G10)

A versioned config, single source of truth for $:

```yaml
# config/pricing.yaml   (USD per 1M tokens unless noted)
providers:
  ollama:        { input: 0.0, output: 0.0 }          # local, free
  qwen-cloud:
    qwen-max:    { input: <verify>, output: <verify> }
    qwen-plus:   { input: <verify>, output: <verify> }
    qwen-turbo:  { input: <verify>, output: <verify> }
  media:
    image:       { unit: "per_image", price: <verify> }
    video:       { unit: "per_second", price: <verify> }
    tts:         { unit: "per_1k_chars", price: <verify> }
```

`cost = tokens_in/1e6 * price.input + tokens_out/1e6 * price.output`. Media uses
unit pricing. `<verify>` values are filled during Sprint 7 against live Qwen Cloud
pricing; until then local mode reports `$0.00` and cloud mode shows
`cost_confidence=estimated`.

### 6.3 Ledger schema (Postgres, resolves G5)

```
skill_invocation
  id, series_id FK, episode_id FK, decision_id, gate, room,
  skill_name, content_hash, model, provider,
  input_tokens, output_tokens, cached_tokens, tokens_estimated bool,
  duration_ms, cost_usd, cost_confidence enum(exact|estimated),
  artifact_id FK?, status enum(ok|failed), created_at

media_generation        # one row per image/video/tts/scene-edit job
  id, episode_id FK, shot_id FK?, kind, provider, model,
  units, unit_cost_usd, cost_usd, duration_ms, status, created_at
```

Both feed the **cost rollup** view per episode/series. The existing
`CostTracker`/`/api/agents/costs` is kept for provider-level totals; these tables
add attribution (series/episode/decision) the PRD requires.

### 6.4 Budget entities (resolves G6)

```
budget
  id, scope enum(series|episode), scope_id,
  limit_usd, soft_pct (default 0.8),
  hard_behavior enum(block|warn) default block,
  spent_usd (materialized), reserved_usd (materialized), created_at
```

A series has a default budget; each episode inherits a per-episode cap. Spend =
Σ `skill_invocation.cost_usd` + Σ `media_generation.cost_usd` within scope.

**Default caps (locked):** `series.limit_usd = 200`, `episode.limit_usd = 20`,
`soft_pct = 0.8`, `hard_behavior = block`. Local Ollama is $0 so caps only bind
in Qwen Cloud mode; values are overridable per series/episode via the budget API.

### 6.5 Reservation protocol (pre-flight, resolves G6)

Expensive operations (a room fan-out, a `produce` run) follow reserve→commit:

1. **Estimate** cost from a heuristic model (avg tokens per skill × #skills;
   shots × per-shot media price). team-cloud-economist (Fin) is also invoked to
   produce the human-facing **cost envelope**; the *enforcement* number is the
   deterministic estimator, not the LLM's.
2. **Reserve** `reserved_usd += estimate` if `spent + reserved + estimate ≤
   limit`; else apply `hard_behavior`.
3. **Commit** on completion: `reserved_usd -= estimate; spent_usd += actual`.
4. Reservations expire (TTL) to avoid leaks on crashed jobs (ARQ job id keyed).

### 6.6 Enforcement points

| Operation | Check |
|---|---|
| `POST /story-room` | reserve estimated room cost; block if over hard cap |
| Episode Greenlight | **pre-flight production estimate** shown as cost review (PRD §5.4); cannot greenlight over hard cap without explicit budget raise |
| `POST /produce` | reserve full shot-plan estimate before any media job dispatches |
| `POST /shots/{id}/regenerate` | reserve single-shot estimate |

Over-soft-cap = warn (visible amber state). Over-hard-cap with `block` = 409 with
a structured `budget_exceeded` payload the UI renders as Fin's veto. This makes
"budget risk" a real gate, satisfying the Production Desk + Cost review promises.

### 6.7 Build-time budgeting (agentic-harness)

The *build* also costs tokens. Reuse harness `tools/bd_tokens.py` +
`.beads/token-ledger.jsonl`: each P0/P1 bead records token totals at close
(`bd_tokens cmd_close`). Set a per-sprint token budget in `.planning/STATUS.md`;
team-cloud-economist reviews build burn the same way it reviews episode cost. This
keeps the "skills used to build = skills used in product" symmetry (PRD §1).

---

## 7. Model Routing (resolves G4/G10)

### 7.1 Two planes, two configs

| Plane | What | Config | Provider |
|---|---|---|---|
| **Skill** | Specialist text judgment | `.harness/models.yaml` tiers (`cheap/balanced/frontier/cheap-with-tools/critic`) | Qwen via Ollama / Qwen Cloud |
| **Media** | image / video / TTS / continuity eval | chrono-canvas `LLMRouter` + `RuntimeConfig` (ConfigHUD) | **Alibaba/Qwen ecosystem (locked):** Wan (Wanxiang) image+video, CosyVoice/Qwen-TTS, via DashScope. Replaces chrono-canvas Gemini media path. |

The product never hardcodes a model. Skills don't pin provider models in SKILL.md
(PRD §7.2). Tier→model mapping is environment-swapped:

```yaml
# local  .harness/models.yaml
cheap: ollama/qwen        balanced: ollama/qwen        frontier: ollama/qwen
cheap-with-tools: ollama/qwen                          critic: ollama/qwen
# cloud  .harness/models.yaml (Sprint 7)
cheap: qwen-cloud/qwen-turbo   balanced: qwen-cloud/qwen-plus
frontier: qwen-cloud/qwen-max  critic: qwen-cloud/qwen-plus  cheap-with-tools: qwen-cloud/qwen-plus
```

### 7.2 Qwen Cloud provider wiring

Qwen Cloud (DashScope, OpenAI-compatible endpoint) is added as a LiteLLM/Pydantic-
AI provider entry in `models.yaml` (base URL + key via env). No orchestration code
change. Cloud mode must record `qwen-cloud` as `provider` on every
`skill_invocation` (acceptance: "Qwen Cloud is load-bearing and visible in audit
traces").

### 7.3 Model-identifier resolution checklist (Sprint 1 + Sprint 7)

1. Confirm exact Ollama tag (e.g. `qwen2.5:7b`/`qwen2.5-coder:14b`) installed.
2. Confirm Qwen Cloud model IDs + base URL + auth.
3. Fill `pricing.yaml` and cloud `models.yaml` from the same IDs.
4. Smoke each tier via `run_skill.py pessimism --model <tier-model> -m "ping"`.

---

## 8. Showrunner Rooms & Approval Gates

### 8.1 Room orchestration pattern

Each room = a product service that (a) builds a canon briefing, (b) fans out
independent single-skill calls (§4) for its roster, (c) persists each
`skill_contribution`, (d) runs the disagreement comparator, (e) emits progress
events, (f) advances the episode state machine.

| Room | Roster (skills) | Output artifacts |
|---|---|---|
| Story Room | creative-director, narrative-engineer, historian, game-designer | branch proposals, beat sheet, choices, accuracy classes, disagreements |
| Production Desk | line-producer, ml-engineer, cloud-economist, frontend-eng, backend-eng, devops-eng | shot plan + dep graph, asset-reuse, media routing, cost envelope, status |
| Greenlight Council | pm, judge-panel, pessimism | scored verdict per gate, ship/defer/reduce/kill |

### 8.2 Episode state machine (resolves G7)

```
DRAFT → STORY_ROOM → BRANCH_GREENLIGHT → EPISODE_PLAN → EPISODE_GREENLIGHT
      → PRODUCING → FINAL_CUT → CANON_COMMIT → DONE
```

- Transitions are explicit endpoints; each is **idempotent** (re-POST returns
  current state, no duplicate fan-out). A `gate` row records actor, verdict,
  dissent snapshot, timestamp.
- Greenlight gates **block** advancement until an approval row exists
  (acceptance: "blocks advancement until approval").
- "Reconsider"/"targeted revision" loops back to the owning room without losing
  prior contributions (append, never overwrite).

### 8.3 Approval without erasing dissent (PRD §4.3)

Approving a gate writes a `decision` referencing the chosen option *and* a
frozen snapshot of all dissenting recommendations. No record is deleted or
rewritten. UI shows the decision with dissent still attached.

### 8.4 Disagreement detection (resolves G3)

Deterministic, no LLM "consensus synthesis" (explicitly forbidden, PRD §4.3):

- Each contribution carries `stance ∈ {support, concern, block}` + `fields`.
- A comparator groups contributions by the decision under review and flags a
  `specialist_disagreement` when stances diverge (any `block`, or mixed
  support/concern on the same axis) or when role-specific fields conflict (e.g.
  historian `accuracy=fiction` vs creative-director `stance=support` on a claim).
- Disagreements are stored and surfaced verbatim; the system never collapses them
  into a single recommendation.

---

## 9. Media Production & Selective Regeneration (resolves G8)

### 9.1 Shot plan & dependency graph

Production Desk emits a `shot` list; each shot has typed inputs (prompt, style
refs, prior-asset reuse) and `depends_on` shot ids → a DAG (rendered with XYFlow,
not as the default UX — PRD §6.2). Stored as `shot.depends_on uuid[]`.

### 9.2 Pipeline reuse

Reuse chrono-canvas LangGraph nodes (`image_generation_node`,
`narration_audio_node`, assembly) and `ProgressPublisher`. Each node call writes a
`media_generation` row (§6.3) and reserves/commits budget (§6.5). Final assembly
produces the 9:16 vertical episode artifact.

### 9.3 Selective regeneration

`POST /shots/{id}/regenerate`:
1. Mark shot + transitive dependents `stale` (DAG walk).
2. Preserve all non-stale approved assets (no full restart — acceptance test).
3. Reserve single-/subgraph cost; regenerate only stale shots.
4. Keep prior version; expose previous-vs-new compare (PRD §5.5).

### 9.4 Continuity evaluation (in-scope for demo, resolves G12)

team-ml-engineer attaches a `critic`-tier eval pass (character/style continuity
score) per shot, **on by default** and surfaced in the Production Desk (locked
decision). Still budget-metered (it costs tokens) and overridable via
`EVAL_ENABLED=false`. Failing scores raise a Production Desk warning, not an
auto-block. Because it uses the critic tier, honor the §7.1 critic caveat
(prefer a non-coding Qwen / `qwen-cloud/qwen-plus`).

---

## 10. Canon / Series Brain (resolves G9)

### 10.1 Entities → tables

PRD §7.4 entities map to SQLAlchemy models (`Base, UUIDMixin, TimestampMixin`):
`series, character, relationship, canon_fact, story_thread, episode,
branch_proposal, beat, shot, audience_choice, canon_mutation, skill_invocation,
skill_contribution, specialist_disagreement, approval_gate, production_artifact`.

### 10.2 Immutable provenance

`canon_mutation` is **append-only**: `id, series_id, episode_id, choice_id?,
mutation_type, payload jsonb, provenance (decision_id/gate), created_at`. Current
canon = fold of mutations (or a materialized snapshot rebuilt from them). No
in-place UPDATE/DELETE of approved choices or canon (enforced by service layer +
DB trigger/role grants). The next Story Room session reads the folded canon
(PRD §5.6 step 5).

---

## 11. API Surface

All PRD §8 endpoints retained. Additions for cost/budgeting & state:

```
# Budget & cost
GET    /api/series/{id}/budget
PUT    /api/series/{id}/budget
GET    /api/episodes/{id}/budget
PUT    /api/episodes/{id}/budget
GET    /api/episodes/{id}/cost              # rollup: skills + media, exact/estimated
POST   /api/episodes/{id}/estimate          # pre-flight production estimate (Fin + estimator)
GET    /api/episodes/{id}/invocations       # skill_invocation ledger (audit)

# State (idempotent)
GET    /api/episodes/{id}                    # status + active room + next gate
```

`POST /greenlights/{gate}` over hard cap → `409 {error:"budget_exceeded", ...}`.
Redis pub/sub remains the only real-time backend channel (PRD §8). Existing
chrono-canvas `/api/agents/costs` kept for provider totals.

---

## 12. Real-time Events

Reuse `services/progress.py::ProgressPublisher` (Redis pub/sub). Channels keyed by
episode id. Event types extend the existing set:
`room_started, skill_contribution_ready, disagreement_detected,
gate_pending, gate_decided, artifact_ready, budget_warning, budget_exceeded,
production_stage, terminal`. Front end consumes via existing SSE/WS bridge; each
event names the contributing skill (authorship labels, PRD §6.3).

---

## 13. Observability & Audit

- `GET /api/episodes/{id}/audit` returns the ordered `skill_invocation` +
  `gate` + `canon_mutation` trail with provider/model/tokens/cost — this is where
  "Qwen Cloud is load-bearing and visible" is demonstrated.
- Reuse request-id middleware + structured logging already in chrono-canvas.
- Cost dashboard surfaces are production artifacts (cost envelope, burn vs
  budget), never a metrics-dominated dashboard (PRD §6.2 avoid-list).

---

## 14. Deployment (Alibaba Cloud)

- Local: `docker-compose` (Postgres, Redis, backend, frontend, Ollama) — extend
  existing chrono-canvas compose files.
- Cloud (Sprint 7): backend on Alibaba Cloud (ECS/container), Postgres + Redis
  managed or containerized, `models.yaml` switched to `qwen-cloud/*`, secrets via
  env. Demo seed series loaded; <3-min demo video; judge-panel + pessimism gates.
- Reuse chrono-canvas `deploy/` + `docker/` scaffolding; record significant
  deltas (PRD Sprint 1).

---

## 15. Build Execution via agentic-harness

Per PRD §9. Concrete engineering notes:

- `harness-init --target=claude --scope=build --shape=sprint-iterative
  --providers=ollama --roster=custom`; `bd init`; `team-onboard` the 13 listed
  skills as **project forks** in `.claude/skills/`. No replacement personas.
- Work tracked as Beads; **every P0/P1 bead requires a `pessimism` review before
  close** (PRD §9.2), and records token totals via `bd_tokens` (§6.7).
- Build skills = product skills (same files), proving the "used in both" promise
  (acceptance: "Updating a project-local skill fork changes product behavior").
- Sprint→bead breakdown follows PRD §9.3 (Harness/Foundation → Skill Runtime →
  Series Brain → Rooms → UI → Media → Cloud/Submission). The Skill Runtime sprint
  must land §4 (bridge) + §5 (contract) + §6.1–6.3 (ledger) before any room work.

---

## 16. Acceptance-Test → Implementation Map

| PRD acceptance test | Mechanism in this TRD |
|---|---|
| SKILL.md loaded, not rewritten | §5.1 registry reads disk; no prompt text in app |
| Every contribution names its skill | §5.4 record + §12 events carry `skill_name` |
| Updating a fork changes behavior | §5.1 fork-first resolution; content_hash per call |
| Works through Qwen on Ollama | §4 bridge + §7.1 local `models.yaml` |
| Cloud records Qwen Cloud as provider | §6.3 `provider` col + §7.2 + §13 audit |
| No monolithic showrunner prompt | §2 invariant; rooms = many single-skill calls |
| Greenlight blocks advancement | §8.2 state machine gates |
| Disagreements remain visible | §8.4 deterministic comparator, no synthesis |
| Approval keeps dissent | §8.3 decision + frozen dissent snapshot |
| Regenerate one shot, no restart | §9.3 DAG-stale walk + asset preservation |
| Canon affects next episode | §10.2 append-only fold read by Story Room |
| Identify room+approval in 10 s | §11 `GET /episodes/{id}` + §6.2 UI |
| Latency shown as production activity | §12 progress events; no spinners |
| Demo <3 min, judge pass, pessimism clean | §14, §15 gates |

---

## 17. Risks & Open Questions

| Risk | Mitigation |
|---|---|
| `HarnessAgent.AgentResult` lacks token counts → cost gaps | §6.1 subprocess+ledger path, else tokenizer estimate flagged `estimated` |
| Qwen Cloud IDs/pricing unknown until late | §7.3 checklist; `<verify>` placeholders; local mode unaffected |
| Local Ollama latency on multi-skill fan-out | §4.4 bounded concurrency + per-skill timeout; async ARQ jobs |
| Skills emit unparseable JSON | §5.3 tolerant parser + raw fallback (never blocks display) |
| Budget reservation leaks on crash | §6.5 TTL reservations keyed by ARQ job id |
| Scope creep into harness (multi-agent) | §2/§4.3 hard invariant; orchestration stays in product |

### 17.1 Resolved decisions (locked 2026-06-06)

1. **Auth/tenancy:** single-tenant — reuse chrono-canvas `app_password` gate. No
   new auth work; multi-user stays out of MVP (PRD §11). The `AuthGateMiddleware`
   already present in the fork is sufficient.
2. **Budget defaults:** hard caps `$20/episode`, `$200/series`,
   `hard_behavior=block`, `soft_pct=0.8` (§6.4). Bind only in Qwen Cloud mode;
   per-scope overridable via budget API.
3. **Continuity eval:** in-scope for the demo, **on by default**, shown in the
   Production Desk (§9.4); `EVAL_ENABLED=false` to disable.
4. **Media stack:** Alibaba/Qwen ecosystem — Wan (image+video) + CosyVoice/Qwen-TTS
   via DashScope (§7.1). Replaces chrono-canvas's Gemini media providers so that
   Qwen Cloud is load-bearing for media too (judging requirement). New provider
   code required (bead under Sprint 6).
5. **Project budget:** $500 total real-spend ceiling; in-app caps $200/series,
   $20/episode (§6.4). Demo-scale output (~3–5 episodes). DashScope credits
   tracked separately; $3k credit prize not assumed pre-award.
6. **Seed series:** Chola Tamil Nadu, 10th c. CE; classic-noir + period aesthetic;
   audience-choice feel "consequential & tense"; vertical 60–90s, standalone-first.
7. **Cloud accounts:** none provisioned yet — Alibaba Cloud + DashScope key setup
   is an explicit Sprint 7 task; develop fully local on Ollama until then.
8. **Deadline & judging:** 2026-07-09 14:00 PDT; weights Tech 30 / Innovation 30 /
   Impact 25 / Presentation 15 (replaces team-judge-panel defaults). See
   `memory/hackathon-facts`.
9. **Skill forks:** verbatim in `backend/showrunner_skills/`; constrained at call
   time (envelope + per-task model tier, cheap model for non-planning) — not by
   editing role text (§5.1, honors PRD §3).
