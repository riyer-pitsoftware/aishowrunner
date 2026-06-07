# UAT Suite 4 — Episode Room UI

Maps to PRD §10 "UI" and §6. Legibility, the persistent 9:16 stage, structured
artifacts (not chat), and honest latency. Requires Sprint 5.

---

### UAT-UI-001 — Identify active room + pending approval within 10s
- **Maps to:** Identify active room and pending approval in 10s · **Priority:** P1 · **Needs:** Sprint 5
- **Method:** Give 3 first-time users the open Episode Room; ask "which room owns this episode and what needs approval next?" Time the answer.
- **Expected:** All answer correctly in ≤10s. Active room occupies the main workspace; other rooms are compact status surfaces; the next required gate is prominent.
- **Result:** ☐  **Evidence:** screen recording + timings

### UAT-UI-002 — Understandable without reading chat logs
- **Maps to:** Interface remains understandable without chat · **Priority:** P1 · **Needs:** Sprint 5
- **Method:** With raw-output panels collapsed, a user explains the episode's current state and each specialist's position.
- **Expected:** State is legible from artifacts (cards, maps, verdicts) alone; no chat transcript required. No raw chain-of-thought shown by default (progressive disclosure only on expand).
- **Result:** ☐  **Evidence:** ______

### UAT-UI-003 — 9:16 episode visible during reviews
- **Maps to:** 9:16 episode remains visible during reviews · **Priority:** P1 · **Needs:** Sprint 5 + 6
- **Steps:** During Production Desk and Greenlight reviews, confirm the persistent 9:16 preview stage stays on screen.
- **Expected:** Preview stage is persistent and correctly 9:16; reviewing does not hide the episode.
- **Result:** ☐  **Evidence:** ______

### UAT-UI-004 — Skill output appears as structured artifacts with authorship
- **Maps to:** Skill output appears as structured artifacts · **Priority:** P1 · **Needs:** Sprint 5
- **Steps:** Inspect a contribution (e.g. Fin cost envelope, game-designer consequence map). Expand it.
- **Expected:** Rendered as a production artifact (card/map), labeled with the contributing skill; expanding reveals full output + invocation metadata (model, tokens, cost). Not a chat bubble.
- **Result:** ☐  **Evidence:** ______

### UAT-UI-005 — Generation latency shown as concrete production activity
- **Maps to:** Generation latency shown as production activity · **Priority:** P1 · **Needs:** Sprint 5 + 6
- **Steps:** Trigger production; observe waiting states.
- **Expected:** Progress is shown as named stages/handoffs (e.g. "Wan rendering shot 3 of 7"), driven by Redis events — never an indefinite spinner.
- **Result:** ☐  **Evidence:** ______
