# UAT Suite 1 — Skill System

Maps to PRD §10 "Skill System". Verifies forks are loaded verbatim, Qwen is the
runtime, contributions are attributed, and there is no monolithic prompt.
Status legend in [../README.md](../README.md).

---

### UAT-SKILL-001 — Skills load from project forks, role text not rewritten
- **Maps to:** SKILL.md loaded without rewriting roles · **Priority:** P0
- **Preconditions:** Backend running (LOCAL). 13 forks in `backend/showrunner_skills/`.
- **Steps:**
  1. `curl -s localhost:8000/api/skills | jq 'length'`
  2. `curl -s localhost:8000/api/skills/team-historian | jq '{name,role_title,content_hash,source_path,body:(.body[0:60])}'`
  3. Open `backend/showrunner_skills/team-historian/SKILL.md` and compare `body` + role title to the file.
- **Expected:** 13 skills listed. `source_path` points under `backend/showrunner_skills/`. Returned `body`/`role_title` are byte-identical to the file (no app-side rewriting). `content_hash` is a 64-char sha256.
- **Result:** ☐  **Evidence:** ______

### UAT-SKILL-002 — No skill prompt text duplicated into source
- **Maps to:** SKILL.md loaded without rewriting roles · **Priority:** P0
- **Steps:**
  1. Grep app source for skill role text: pick a distinctive sentence from a SKILL.md and search `backend/src/`.
  2. Confirm the only copies live under `backend/showrunner_skills/` (the forks).
- **Expected:** No specialist role/persona prose embedded in `backend/src/`. The product references skills by file, never by inlined prompt.
- **Result:** ☐  **Evidence:** ______

### UAT-SKILL-003 — Every contribution names its source skill
- **Maps to:** Every contribution identifies its skill · **Priority:** P0
- **Preconditions:** A skill invocation has run (any room or the smoke).
- **Steps:**
  1. Inspect a `SkillCallResult` / `skill_invocations` row (or the room contribution artifact).
  2. Confirm `skill_name`, `model`, `provider`, `content_hash` are populated.
- **Expected:** Result/record carries the originating `skill_name` and the resolved model — attribution is never anonymous.
- **Result:** ☐  **Evidence:** ______

### UAT-SKILL-004 — Updating a fork changes product behavior
- **Maps to:** Updating a project-local fork changes behavior · **Priority:** P0
- **Steps:**
  1. `GET /api/skills/team-historian` → note `content_hash` (H1).
  2. Append a line to `backend/showrunner_skills/team-historian/SKILL.md`.
  3. `GET /api/skills/team-historian` again → `content_hash` (H2).
  4. Invoke the historian and observe the body reaching the model (or the new instruction reflected).
  5. Revert the file.
- **Expected:** `H2 ≠ H1`; the new instruction is present in the loaded body and influences output. Confirms fork-first, no caching of stale role text.
- **Result:** ☐  **Evidence:** ______

### UAT-SKILL-005 — Skill invocation works through Qwen on Ollama
- **Maps to:** Skill invocations work through Qwen on Ollama · **Priority:** P0
- **Preconditions:** Ollama running with a Qwen model; `.harness/models.yaml` tiers → `ollama/qwen*`.
- **Steps:**
  1. Run the smoke: `cd backend && PYTHONPATH=src python -m pytest tests/showrunner/test_skill_smoke.py -q` **or**
  2. `echo "ship it" | ~/code/agentic-harness/runtime/run_skill.py pessimism -v`
- **Expected:** Returns Qwen-generated text; verbose header shows `model: ollama/qwen…` resolved from the project `models.yaml`.
- **Result:** ☐  **Evidence:** ______

### UAT-SKILL-006 — Cloud mode records Qwen Cloud as the provider
- **Maps to:** Cloud mode records Qwen Cloud · **Priority:** P0 · **Env:** CLOUD
- **Preconditions:** `.harness/models.yaml` tiers → `qwen-cloud/*`; DashScope key set.
- **Steps:**
  1. Invoke any skill in CLOUD mode.
  2. Inspect the `skill_invocations` row / audit trace.
- **Expected:** `provider = "qwen-cloud"` and `model` is a Qwen Cloud id; appears in `/api/episodes/{id}/audit`.
- **Result:** ☐  **Evidence:** ______

### UAT-SKILL-007 — No monolithic showrunner prompt
- **Maps to:** No monolithic showrunner prompt exists · **Priority:** P1
- **Steps:**
  1. Review the orchestration code (`chronocanvas.showrunner.*`).
  2. Confirm rooms compose **many single-skill** calls via `SkillPort`; there is no single "showrunner agent" mega-prompt, and harness Layer B remains single-skill.
- **Expected:** No god-prompt; each specialist invoked independently with its own fork.
- **Result:** ☐  **Evidence:** ______
