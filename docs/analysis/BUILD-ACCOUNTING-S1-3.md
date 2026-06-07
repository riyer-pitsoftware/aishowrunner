# Build Accounting & Budget Analysis — Sprints 1–3

Prepared for budget review (team-cloud-economist / Fin lens) and PM analysis
(Kenji). Period: 2026-06-06 → 2026-06-07. Source data: git history, Beads,
`.beads/token-ledger.jsonl`, `config/pricing.yaml` (pending), role estimation
heuristics. See [[hackathon-facts]]: deadline 2026-07-09, $500 real cap,
$3,000 cloud credits.

## 1. Headline

| Metric | Value |
|---|---|
| **Real cloud/$ spend to date** | **$0.00** (local Ollama only; no cloud accounts provisioned) |
| Budget consumed | $0 of $500 cap · 0% · $3,000 credits untouched |
| Build LLM tokens (metered, Qwen/Ollama) | 9,932 tokens over 9 skill invocations → $0 |
| Sprints complete | 3 of 7 |
| Beads closed | 21 of 61 (34%) |
| Authored output | ~4,107 lines (1,891 code · 464 tests · 1,752 docs) |
| Inherited (ChronoCanvas fork) | ~66,500 lines (reused, not authored) |
| Automated tests | 30 passing (showrunner subset); ruff clean |
| Pessimism gates passed | 3 (one per sprint) |

**Posture: on schedule, $0 burned, all spend deferred to Sprints 6–7.** The
cost-control subsystem (epic `asr-3mk`) lands *before* the first dollar is spent.

## 2. Scope delivered (beads closed)

| Sprint | Epic | Tasks closed | Output |
|---|---|---|---|
| 1 — Harness & Foundation | asr-497 | 6/6 | harness init, lightweight ChronoCanvas fork + reusable kit, 13 skill forks, 12 role memories, Qwen/Ollama routing |
| 2 — Skill Runtime & Bridge | asr-0bj | 8/8 | SkillPort, HarnessSkillPort (litellm, token capture), SubprocessSkillPort, registry, envelopes/parser, fan-out, invocation ledger, `/api/skills` |
| 3 — Series Brain | asr-63f | 4/4 | 16 entity models, append-only canon + immutability guards, canon fold, episode state machine, `/api/series` + `/canon`, migration 010, UAT pack |

Closed incl. epics: **21 beads**. Remaining: 40 (Cost & Budgeting, Rooms, UI,
Media, Cloud/Submission).

## 3. Output accounting (what was built)

| Category | Lines | Notes |
|---|---|---|
| Product code (showrunner pkg + models + routes + schemas + migration) | 1,891 | authored |
| Automated tests | 464 | 30 cases, incl. real Ollama smoke |
| Docs — PRD + TRD + UAT (9 files) | 1,752 | UAT ≈ 40 cases, full traceability |
| **Authored subtotal** | **4,107** | |
| Installed skill forks (verbatim) | 1,454 | copied, not authored |
| Inherited ChronoCanvas fork | ~66,500 | reused framework (FastAPI/React/LangGraph/…) |

**Leverage:** ~66.5k lines of proven foundation reused for ~4.1k lines of
authored integration — the fork strategy is the single biggest cost saver.

## 4. LLM / token accounting

Source: `.beads/token-ledger.jsonl` (harness `run_skill.py` auto-logs usage).

| Item | Calls | Tokens | $ |
|---|---|---|---|
| Skill invocations on Qwen/Ollama (pessimism gates + smokes) | 9 | 9,932 | $0.00 (local) |

**Known measurement gap:** the Claude Code *orchestration* tokens used to build
the app are **not** in the ledger — the harness Stop hook was not wired into
`.claude/settings.local.json` during this build (harness-init flagged this). Those
are build-assistant credits (excluded from project budget by Fin's rules anyway),
but per-bead orchestration attribution is therefore unavailable. *Remediation:*
wire the Stop hook before Sprint 4 if per-bead token attribution is wanted
(low priority — it doesn't affect real $).

## 5. Real-dollar budget accounting (Fin)

Per role rules (`memory/team/cloud-economist`): only real cloud/API spend counts;
local Ollama, Claude credits, and virtual-team estimates do **not**.

| Budget line | Cap | Used | Remaining |
|---|---|---|---|
| Project real cash | $500 | **$0.00** | $500 |
| Per-series (in-app) | $200 | $0.00 | $200 |
| Per-episode (in-app) | $20 | $0.00 | $20 |
| DashScope cloud credits | $3,000 | $0.00 | $3,000 |

Nothing has been provisioned or spent. All Sprints 1–3 ran on local Ollama
(skill text) with no media generation and no cloud deployment.

## 6. Notional effort / value analysis (analysis only — NOT budget)

Engineer-hours estimated from the onboarded roles' estimation heuristics, valued
at their configured rates. This is a *value* lens (what this would cost as paid
engineering); it is **not** money spent.

| Sprint | Hours (est.) | Primary roles | Notional value |
|---|---|---|---|
| 1 — Foundation | ~13 | Devon/Suki/Kenji | ~$1,900 |
| 2 — Skill Runtime | ~35 | Suki (bridge) + Priya | ~$5,400 |
| 3 — Series Brain + UAT | ~41 | Priya + docs | ~$5,400 |
| **Total** | **~89 h** | | **~$12,700** |

Rates: Priya (backend) $145, Suki (ML) $165, Devon (devops) $145, docs ~$90.
Treat ±30% (AI-assisted build compresses wall-clock far below these hours).

## 7. Velocity & burn-down

- 21/61 beads closed in 3/7 sprints. Bead-completion ≈ on the linear pace needed
  for the 2026-07-09 deadline (≈ 32 days out), with the heaviest remaining work
  (Rooms, UI, Media) front-loadable now that the substrate + canon exist.
- Quality gates held: every P0/P1 sprint passed a pessimism review; 30 automated
  tests; zero lint debt introduced.

## 8. Forward cost outlook (where the money will go)

| Sprint | Real-$ risk | Notes |
|---|---|---|
| 4 — Rooms & Gates | ~$0 (local) | Skill fan-out on Ollama; Qwen Cloud only in CLOUD mode |
| 5 — UI | $0 | frontend only |
| 6 — Media Production | **first real spend** | Alibaba Wan (image/video) + CosyVoice (TTS) via DashScope; unit prices TBD in `config/pricing.yaml` (asr-av5.2). Demo-scale 3–5 episodes |
| 7 — Cloud & Submission | hosting + Qwen Cloud text | Alibaba Cloud compute + Qwen Cloud inference (cheap per token) |

**Rough envelope (to validate once `pricing.yaml` is filled):** a demo of 3–5
episodes at ~10 shots each is expected to land in the low-tens of dollars of media
spend — comfortably inside the $500 cap and the $3,000 credit pool. The budget
**enforcement** engine (`asr-3mk`: reserve→commit, hard caps, `409 budget_exceeded`)
is the immediate next epic, so spend is metered and capped *before* Sprint 6.

## 9. Recommendations

1. **Build `asr-3mk` (Cost & Budgeting) next** — it must precede media spend (Sprint 6). ✅ already the next ready epic.
2. **Fill `config/pricing.yaml`** with verified DashScope Wan/CosyVoice/Qwen prices early (part of asr-av5.2) so estimates are real, not placeholders.
3. **Provision the Alibaba/DashScope account** on a small budget; confirm Qwen Cloud model IDs (asr-av5.1) to de-risk Sprint 7.
4. **(Optional)** wire the harness Stop hook for per-bead build-token attribution.
5. Keep the fork-leverage discipline: prefer reuse of ChronoCanvas pipeline over net-new in Media (Sprint 6) to hold cost down.
