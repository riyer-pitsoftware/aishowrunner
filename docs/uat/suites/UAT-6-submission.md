# UAT Suite 6 — Submission Readiness

Maps to PRD §10 "Submission" and the hackathon hard requirements
(`memory/hackathon-facts`). All P0 here gate the submission. Needs Sprint 7.

---

### UAT-SUB-001 — Qwen Cloud is load-bearing and visible in audit
- **Maps to:** Qwen Cloud load-bearing + visible · **Priority:** P0 · **Env:** CLOUD
- **Steps:** Run a full episode in CLOUD; `GET /api/episodes/{id}/audit`.
- **Expected:** Skill intelligence resolves to Qwen Cloud (`provider=qwen-cloud`); media via Alibaba Wan/CosyVoice; audit trace shows Qwen Cloud calls with model + tokens. Disabling Qwen Cloud breaks core function (proves load-bearing, not decorative).
- **Result:** ☐  **Evidence:** audit export

### UAT-SUB-002 — Public OSS repo documents post-2026-05-26 work + license
- **Maps to:** Public repo + detectable license · **Priority:** P0
- **Steps:** Open the public GitHub repo; verify `LICENSE`, README, and commit history dated after 2026-05-26.
- **Expected:** Repo public; detectable license present; history shows the build (Sprints 1+).
- **Result:** ☐  **Evidence:** repo URL

### UAT-SUB-003 — Alibaba Cloud deployment demonstrated
- **Maps to:** Proof of Alibaba Cloud deployment · **Priority:** P0 · **Needs:** Sprint 7
- **Steps:** Hit the deployed Alibaba Cloud URL; complete a core action.
- **Expected:** App reachable on Alibaba Cloud; backend serves requests; screenshot/console proof captured.
- **Result:** ☐  **Evidence:** URL + console screenshot

### UAT-SUB-004 — Demo video under ~3 minutes
- **Maps to:** Demo video < 3 min · **Priority:** P0
- **Steps:** Review the recorded demo on YouTube/Vimeo/Facebook.
- **Expected:** Runtime ≤ ~3:00; shows the create→produce→choose loop and Qwen Cloud usage; hosted on an allowed platform.
- **Result:** ☐  **Evidence:** video URL + duration

### UAT-SUB-005 — Judge Panel returns a passing verdict
- **Maps to:** Judge Panel passing verdict · **Priority:** P1 · **Needs:** Sprint 7
- **Steps:** Run the `team-judge-panel` skill against the submission using the real weights (Tech 30 / Innovation 30 / Impact 25 / Presentation 15).
- **Expected:** Passing scored verdict; weak axes have remediation notes.
- **Result:** ☐  **Evidence:** verdict artifact

### UAT-SUB-006 — Pessimism finds no unsupported completion claims
- **Maps to:** Pessimism review clean · **Priority:** P1 · **Needs:** Sprint 7
- **Steps:** Run `pessimism` over the submission claims (Qwen Cloud, Alibaba, demo, repo).
- **Expected:** Every claim has verifiable evidence; no hand-waving flagged.
- **Result:** ☐  **Evidence:** pessimism output

### UAT-SUB-007 — Architecture diagram present
- **Maps to:** Architecture diagram required · **Priority:** P0
- **Steps:** Locate the rendered architecture diagram (repo + submission).
- **Expected:** A clear diagram of the 3-layer architecture (UI / orchestration with Skill+Media planes / data) exists and matches the build.
- **Result:** ☐  **Evidence:** diagram file

### UAT-SUB-008 — Track identified as AI Showrunner
- **Maps to:** Track identified · **Priority:** P0
- **Steps:** Check the Devpost submission + README declare Track 2 (AI Showrunner).
- **Expected:** Track explicitly stated.
- **Result:** ☐  **Evidence:** submission screenshot
