# UAT Suite 5 — Cost & Budgeting

Maps to TRD §6 and the hackathon's budget credibility. Every call metered + priced
+ attributed; budgets enforced via reserve→commit; hard caps block. Needs the
Cost & Budgeting epic (`asr-3mk`).

---

### UAT-COST-001 — Every skill call is metered and attributed
- **Maps to:** TRD §6.1/§6.3 · **Priority:** P1 · **Partially now**
- **Steps:** Invoke a skill (any room or smoke). Inspect `skill_invocations`.
- **Expected:** Row records `input_tokens`, `output_tokens`, `tokens_estimated`, `model`, `provider`, `content_hash`, and attribution (`series_id`/`episode_id`/`decision_id`/`room`). When tokens are estimated, `cost_confidence='estimated'`.
- **Result:** ☐  **Evidence:** ______

### UAT-COST-002 — Every media job is metered and priced
- **Maps to:** TRD §6.3 · **Priority:** P1 · **Needs:** Sprint 6
- **Steps:** Produce/regenerate; inspect `media_generation` rows.
- **Expected:** One row per image/video/TTS job with units, unit cost, and `cost_usd` from `config/pricing.yaml`; attributed to episode/shot.
- **Result:** ☐  **Evidence:** ______

### UAT-COST-003 — Pre-flight estimate at Episode Greenlight
- **Maps to:** TRD §6.6 · **Priority:** P1 · **Needs:** Cost epic + Sprint 4
- **Steps:** At Episode Greenlight, `POST /api/episodes/{id}/estimate` (or view the cost review).
- **Expected:** A deterministic production-cost estimate is shown (skills × avg + shots × media price) alongside Fin's human-facing envelope; reserved before any media runs.
- **Result:** ☐  **Evidence:** ______

### UAT-COST-004 — Reserve→commit: no double-spend, no leak
- **Maps to:** TRD §6.5 · **Priority:** P1 · **Needs:** Cost epic
- **Steps:**
  1. Note `budget.reserved_usd`/`spent_usd`. Start a produce run → reserved rises.
  2. On completion → reserved falls, spent rises by **actual**.
  3. Kill a run mid-flight → reservation expires (TTL), not leaked.
- **Expected:** Accounting balances; estimates reserve, actuals commit; crashed jobs don't permanently hold budget.
- **Result:** ☐  **Evidence:** ______

### UAT-COST-005 — Hard cap blocks with structured error
- **Maps to:** TRD §6.6 · **Priority:** P1 · **Needs:** Cost epic
- **Steps:** Set episode budget low (e.g. `$0.01`, CLOUD). Attempt produce / greenlight.
- **Expected:** `409` with `{"error":"budget_exceeded", ...}`; the operation does not dispatch media; UI renders it as Fin's veto. Raising the budget unblocks.
- **Result:** ☐  **Evidence:** ______

### UAT-COST-006 — Soft cap warns without blocking
- **Maps to:** TRD §6.6 · **Priority:** P2 · **Needs:** Cost epic
- **Steps:** Drive spend past `soft_pct` (0.8) but under the hard cap.
- **Expected:** A `budget_warning` event + visible amber state; work continues.
- **Result:** ☐  **Evidence:** ______

> Note (LOCAL): Ollama is `$0`, so caps only bind in CLOUD/Qwen-Cloud mode. For
> LOCAL enforcement testing, set a near-zero cap and use the pricing override.
