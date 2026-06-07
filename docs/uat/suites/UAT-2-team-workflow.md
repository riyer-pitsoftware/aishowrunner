# UAT Suite 2 — Team Workflow

Maps to PRD §10 "Team Workflow". Rooms convene the right specialists, gates block
advancement, and disagreement is preserved (never synthesized away).

**Sprint 4 status:** endpoints implemented (`POST /series/{id}/story-room`,
`/episodes/{id}/production-desk`, `/greenlights/{gate}`; `GET
/episodes/{id}/contributions|disagreements`). The deterministic cores
(comparator, gate mapping, rosters, dissent snapshot) are unit-tested (16 tests).
Live execution below needs a running Postgres + Ollama (tracked: asr-05c).

---

### UAT-TEAM-001 — Story Room invokes all required specialists
- **Maps to:** Story Room invokes all required skills · **Priority:** P0 · **Sprint 4: endpoint live; run needs DB+Ollama**
- **Preconditions:** A series exists; episode in `story_room`.
- **Steps:**
  1. `POST /api/series/{id}/story-room`.
  2. `GET /api/episodes/{id}/contributions`.
- **Expected:** Exactly one contribution each from `team-creative-director`, `team-narrative-engineer`, `team-historian`, `team-game-designer`; each names its skill and resolved Qwen model.
- **Result:** ☐  **Evidence:** ______

### UAT-TEAM-002 — Production Desk invokes the production specialists
- **Maps to:** Production Desk invokes appropriate skills · **Priority:** P0 · **Sprint 4: endpoint live; run needs DB+Ollama**
- **Steps:**
  1. Advance an approved episode into Production Desk.
  2. `GET /api/episodes/{id}/contributions?room=production_desk`.
- **Expected:** Contributions from line-producer, ml-engineer, cloud-economist, frontend, backend, devops (per PRD §4.2); cost envelope present from Fin.
- **Result:** ☐  **Evidence:** ______

### UAT-TEAM-003 — Greenlight blocks advancement until approval
- **Maps to:** Greenlight Council blocks advancement · **Priority:** P0 · **Sprint 4: endpoint live; run needs DB+Ollama**
- **Steps:**
  1. With an episode at `branch_greenlight`, attempt to advance to production **without** posting a greenlight.
  2. Then `POST /api/episodes/{id}/greenlights/branch` with an approval and retry.
- **Expected:** Step 1 is rejected (state cannot skip the gate). Step 2 succeeds and the episode advances. Episode state machine (TRD §8.2) enforces it.
- **Result:** ☐  **Evidence:** ______

### UAT-TEAM-004 — Disagreements remain visible
- **Maps to:** Disagreements remain visible · **Priority:** P0 · **Sprint 4: endpoint live; run needs DB+Ollama**
- **Preconditions:** Construct a scenario where the historian flags `block`/`concern` while the creative director `support`s (e.g. an anachronistic but dramatic beat).
- **Steps:**
  1. Convene the room. `GET /api/episodes/{id}/disagreements`.
- **Expected:** A `specialist_disagreement` record lists the divergent stances per skill verbatim; no averaged/merged "consensus". UI shows it explicitly.
- **Result:** ☐  **Evidence:** ______

### UAT-TEAM-005 — Approval keeps dissenting recommendations
- **Maps to:** Approval selects a decision without erasing dissent · **Priority:** P0 · **Sprint 4: endpoint live; run needs DB+Ollama**
- **Steps:**
  1. With a recorded disagreement, approve a gate choosing one option.
  2. Inspect the `approval_gate` record and the prior contributions.
- **Expected:** The decision references the chosen option **and** a frozen `dissent_snapshot`; original dissenting contributions are unchanged (immutability). Nothing is rewritten or deleted.
- **Result:** ☐  **Evidence:** ______
