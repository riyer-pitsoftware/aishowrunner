# UAT Suite 3 — Product Workflow (end-to-end)

Maps to PRD §10 "Product Workflow" and §5 primary user workflow. The full loop:
create → story room → branch → plan → produce → final cut → choice → canon.
Series/canon steps are executable now (Sprint 3); the rest need Sprints 4–6.

---

### UAT-PROD-001 — Create a series
- **Maps to:** Create a series · **Priority:** P0 · **Executable now**
- **Steps:**
  1. `curl -s -XPOST localhost:8000/api/series -H 'content-type: application/json' -d '{"title":"The Thanjavur Ledger","era":"Chola Tamil Nadu, 10th c.","premise":"A temple accountant uncovers a conspiracy."}'`
  2. `curl -s localhost:8000/api/series | jq`
  3. `curl -s localhost:8000/api/series/{id} | jq`
- **Expected:** 201 with a series id; series appears in the list and by id; `era`/`premise` persisted.
- **Result:** ☐  **Evidence:** ______

### UAT-PROD-002 — Convene the Story Room
- **Maps to:** Convene the Story Room · **Priority:** P0 · **Sprint 4: endpoint live; run needs DB+Ollama**
- **Steps:** `POST /api/series/{id}/story-room`; poll `/api/episodes/{id}/events`.
- **Expected:** An episode is created in `story_room`; specialist contributions stream in; 2–3 branch proposals produced and sent to Branch Greenlight.
- **Result:** ☐  **Evidence:** ______

### UAT-PROD-003 — Review and approve a branch
- **Maps to:** Review and approve a branch · **Priority:** P0 · **Sprint 4: endpoint live; run needs DB+Ollama**
- **Steps:** Inspect proposals (hook, consequences, historical notes, complexity); `POST /api/episodes/{id}/greenlights/branch` selecting one.
- **Expected:** Selected branch recorded; episode advances to `episode_plan`. "Reconsider" instead loops back to `story_room` without losing proposals.
- **Result:** ☐  **Evidence:** ______

### UAT-PROD-004 — Approve the episode plan
- **Maps to:** Approve an episode plan · **Priority:** P0 · **Sprint 4: endpoint live; run needs DB+Ollama** + 5
- **Steps:** Review beat sheet + closing choices (Story Room) and shot list + budget (Production Desk); review the Greenlight pack (creative/narrative/historical/feasibility/cost/judge); `POST /greenlights/episode`.
- **Expected:** Plan approved with a visible **pre-flight cost estimate** (UAT-COST-003); episode → `producing`. Over hard cap is blocked (UAT-COST-005).
- **Result:** ☐  **Evidence:** ______

### UAT-PROD-005 — Produce the episode
- **Maps to:** Produce the episode · **Priority:** P0 · **Needs:** Sprint 6
- **Steps:** `POST /api/episodes/{id}/produce`; watch `/events` for `artifact_ready`/`production_stage`.
- **Expected:** Shots generate per the dependency graph; assets appear; a 9:16 episode assembles. Each media job recorded in `media_generation` with cost.
- **Result:** ☐  **Evidence:** ______

### UAT-PROD-006 — Regenerate one shot without restarting
- **Maps to:** Regenerate one shot without restarting · **Priority:** P0 · **Needs:** Sprint 6
- **Steps:** Pick a completed shot; `POST /api/episodes/{id}/shots/{shot_id}/regenerate`.
- **Expected:** Only that shot + its transitive dependents go `stale` and regenerate; all other approved assets are preserved; previous version retained for compare (TRD §9.3).
- **Result:** ☐  **Evidence:** ______

### UAT-PROD-007 — Approve the final cut
- **Maps to:** Approve the final cut · **Priority:** P0 · **Sprint 4: endpoint live; run needs DB+Ollama** + 6
- **Steps:** Review assembled 9:16; `POST /api/episodes/{id}/finalize` then `POST /greenlights/final`.
- **Expected:** Final cut approved; episode → `canon_commit`; assembled artifact recorded.
- **Result:** ☐  **Evidence:** ______

### UAT-PROD-008 — Select the ending choice
- **Maps to:** Select the ending choice · **Priority:** P0 · **Sprint 4: endpoint live; run needs DB+Ollama**
- **Steps:** `GET /api/episodes/{id}/choices`; `POST /api/episodes/{id}/choices/{choice_id}/select`.
- **Expected:** game-designer proposes state changes, narrative-engineer + historian review, selected consequences become **canon mutations** with provenance; the choice is then frozen (cannot be changed).
- **Result:** ☐  **Evidence:** ______

### UAT-PROD-009 — Canon changes affect the next episode
- **Maps to:** Verify canon changes affect the next episode · **Priority:** P0 · **Partially executable now**
- **Steps (Sprint 3 slice, executable now):**
  1. Append canon via the service / a mutation, then `GET /api/series/{id}/canon`.
  2. Confirm the fold reflects added facts/threads and excludes retired ones.
- **Steps (full, Sprint 4):** Select a choice in episode N; convene Story Room for N+1; confirm the briefing includes the new canon.
- **Expected:** `GET /canon` is the fold of the append-only mutation log; the next Story Room session receives the updated state.
- **Result:** ☐  **Evidence:** ______
