# AI Showrunner PRD

  Target file: docs/PRD.md
  Build workspace: /Users/riyer/code/qwencloud-aishowrunner
  Foundation: /Users/riyer/code/chrono-canvas
  Execution system: /Users/riyer/code/agentic-harness

  ## 1. Product Definition

  AI Showrunner is a persistent production workspace for creating audience-steered, 60–90 second vertical historical-noir episodes.

  The product is operated by visible showrunner teams composed exclusively from the existing Claude team-* skills. It must not introduce replacement personas or duplicate role definitions.

  Each skill retains its existing expertise, personality, rubric, and onboarding configuration. The same skills are used:

  1. By Claude and agentic-harness to build the application.
  2. Inside the shipped application to plan, review, produce, and approve episodes.

  Qwen supplies the model intelligence used when invoking these skills:

  - Local development: Qwen through Ollama.
  - Hackathon deployment: Qwen through Qwen Cloud.

  The product is not a chatbot and does not contain a single monolithic “showrunner agent.” It is a coordinated team production system.

  ## 2. Product Promise

  > Assemble a showrunner team, give it a series premise, and repeatedly produce audience-steered episodes that preserve canon and improve through specialist review.

  A user should always be able to see:

  - Which room currently owns the episode.
  - Which skills are participating.
  - What each specialist recommended.
  - Where specialists disagree.
  - What requires human approval.
  - Which decisions became series canon.

  ## 3. Existing Skill Constraint

  Only existing Claude skills may define showrunner roles.

  Canonical skills are sourced from:

  ~/.claude/skills/<skill-name>/SKILL.md

  Project-owned forks are installed through team-onboard into:

  .claude/skills/<skill-name>/SKILL.md

  The product must load skill instructions from these files. Skill prompts must not be copied into application source code or rewritten as application-specific personas.

  Project-specific behavior belongs in the existing per-role memory configuration:

  ~/.claude/projects/-Users-riyer-code-qwencloud-aishowrunner/memory/team/

  ## 4. Showrunner Teams

  ### 4.1 Story Room

  The Story Room develops the series, episode structure, and audience choices.


• Proposed Plan


  # AI Showrunner PRD

  Target file: docs/PRD.md
  Build workspace: /Users/riyer/code/qwencloud-aishowrunner
  Foundation: /Users/riyer/code/chrono-canvas
  Execution system: /Users/riyer/code/agentic-harness

  ## 1. Product Definition

  AI Showrunner is a persistent production workspace for creating audience-steered, 60–90 second vertical historical-noir episodes.

  The product is operated by visible showrunner teams composed exclusively from the existing Claude team-* skills. It must not introduce replacement personas or duplicate role definitions.

  Each skill retains its existing expertise, personality, rubric, and onboarding configuration. The same skills are used:

  1. By Claude and agentic-harness to build the application.
  2. Inside the shipped application to plan, review, produce, and approve episodes.

  Qwen supplies the model intelligence used when invoking these skills:

  - Local development: Qwen through Ollama.
  - Hackathon deployment: Qwen through Qwen Cloud.

  The product is not a chatbot and does not contain a single monolithic “showrunner agent.” It is a coordinated team production system.

  ## 2. Product Promise

  > Assemble a showrunner team, give it a series premise, and repeatedly produce audience-steered episodes that preserve canon and improve through specialist review.

  A user should always be able to see:

  - Which room currently owns the episode.
  - Which skills are participating.
  - What each specialist recommended.
  - Where specialists disagree.
  - What requires human approval.
  - Which decisions became series canon.

  ## 3. Existing Skill Constraint

  Only existing Claude skills may define showrunner roles.

  Canonical skills are sourced from:

  ~/.claude/skills/<skill-name>/SKILL.md

  Project-owned forks are installed through team-onboard into:

  .claude/skills/<skill-name>/SKILL.md

  The product must load skill instructions from these files. Skill prompts must not be copied into application source code or rewritten as application-specific personas.

  Project-specific behavior belongs in the existing per-role memory configuration:

  ~/.claude/projects/-Users-riyer-code-qwencloud-aishowrunner/memory/team/

  ## 4. Showrunner Teams

  ### 4.1 Story Room

  The Story Room develops the series, episode structure, and audience choices.

   Existing skill             Responsibility
  ━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   team-creative-director     Protect the historical-noir identity and judge whether creative decisions serve the story.
  ─────────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────
   team-narrative-engineer    Design hooks, episode beats, pacing, retention, cliffhangers, and multi-episode arcs.
  ─────────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────
   team-historian             Review historical accuracy, regional specificity, material culture, and uncertainty.
  ─────────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────
   team-game-designer         Design audience choices, consequence previews, branching state, and meaningful tradeoffs.

  The Story Room produces:

  - Series premise and creative rules.
  - Relevant canon briefing.
  - Two or three next-episode branch proposals.
  - Episode beat sheet.
  - Closing audience choices.
  - Historical accuracy and fiction classifications.
  - Explicit disagreements between specialists.

  ### 4.2 Production Desk

  The Production Desk converts an approved episode into producible assets.

   Existing skill            Responsibility
  ━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   team-line-producer        Own production feasibility, scheduling, asset reuse, shot scope, and production risk.
  ────────────────────────  ───────────────────────────────────────────────────────────────────────────────────────
   team-ml-engineer          Select and validate Qwen, image, video, TTS, and continuity-evaluation workflows.
  ────────────────────────  ───────────────────────────────────────────────────────────────────────────────────────
   team-cloud-economist      Estimate and monitor episode cost, provider spend, and budget risk.
  ────────────────────────  ───────────────────────────────────────────────────────────────────────────────────────
   team-frontend-engineer    Own the Episode Room interaction quality and visible production state.
  ────────────────────────  ───────────────────────────────────────────────────────────────────────────────────────
   team-backend-engineer     Own persistent canon, orchestration, jobs, APIs, and failure recovery.
  ────────────────────────  ───────────────────────────────────────────────────────────────────────────────────────
   team-devops-engineer      Own local runtime, Alibaba Cloud deployment, observability, and demo reliability.

  The Production Desk produces:

  - Shot plan and dependency graph.
  - Asset-reuse recommendations.
  - Media-provider routing plan.
  - Cost estimate and production budget.
  - Production status and failure-recovery actions.
  - Final assembled vertical episode.

  ### 4.3 Greenlight Council

  The Greenlight Council decides whether work advances.

   Existing skill      Responsibility
  ━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   team-pm             Make ship, defer, reduce, or kill decisions against deadline and judging criteria.
  ──────────────────  ────────────────────────────────────────────────────────────────────────────────────
   team-judge-panel    Evaluate UX, technical depth, demo visibility, and emotional impact.
  ──────────────────  ────────────────────────────────────────────────────────────────────────────────────
   pessimism           Challenge unsupported completion claims and require verification.

  The Greenlight Council owns three approval gates:

  1. Branch Greenlight: select the next episode direction.
  2. Episode Greenlight: approve the beat sheet and production plan.
  3. Final Cut: approve the assembled episode and canon mutations.

  Substantive disagreement must remain visible. The system must not silently synthesize conflicting reviews into false consensus.

  ## 5. Primary User Workflow

  ### 5.1 Open The Episode Room

  The user opens an existing historical-noir series.

  The workspace immediately shows:

  - Current canon.
  - Characters and relationships.
  - Unresolved story threads.
  - Previous audience choice.
  - Current episode status.
  - Active room and participating skills.
  - Next required approval.

  ### 5.2 Convene The Story Room

  The user starts the next episode.

  The system:

  1. Retrieves relevant series canon.
  2. Invokes the Story Room skills independently.
  3. Shows each specialist’s contribution.
  4. Identifies agreements and disagreements.
  5. Produces two or three branch proposals.
  6. Sends the proposals to Branch Greenlight.

  ### 5.3 Greenlight A Branch

  Each proposal shows:

  - Hook and dramatic promise.
  - Character consequences.
  - Historical considerations.
  - New and resolved story threads.
  - Audience-choice potential.
  - Estimated production complexity.

  The user selects a branch or asks the Story Room to reconsider it.

  ### 5.4 Approve The Episode Plan

  The Story Room creates the beat sheet and closing choices.

  The Production Desk converts the plan into a shot list, budget, and generation strategy.

  The Greenlight Council presents:

  - Creative review.
  - Narrative-retention review.
  - Historical review.
  - Production-feasibility review.
  - Cost review.
  - Judge-panel verdict.

  The user approves or requests targeted revisions.

  ### 5.5 Produce And Review

  The Production Desk generates assets and assembles the episode.

  The user can:

  - Inspect the current production stage.
  - Review specialist warnings.
  - Regenerate an individual shot.
  - Preserve unaffected approved assets.
  - Compare previous and regenerated versions.
  - Review the final vertical episode.

  ### 5.6 Commit Audience Choice

  The completed episode ends with two or three meaningful choices.

  After selection:

  1. team-game-designer proposes state changes.
  2. team-narrative-engineer reviews future narrative value.
  3. team-historian flags historical implications.
  4. The selected consequences become persistent canon.
  5. The next Story Room session receives the updated state.

  ## 6. User Interface

  ### 6.1 Core Layout

  The main interface is an Episode Room with three visible workspaces:

  - Story Room: canon rail, branch proposals, beat board, and specialist discussion.
  - Production Desk: shot timeline, asset states, costs, dependencies, and preview stage.
  - Greenlight Council: pending approvals, specialist verdicts, disagreements, and evidence.

  The active room occupies the main workspace. The other rooms remain visible as compact status surfaces.

  ### 6.2 UI Principles

  Use:

  - A production-desk metaphor rather than chat.
  - Warm charcoal, paper white, oxidized brass, and restrained status colors.
  - Strong editorial typography.
  - A persistent 9:16 preview stage.
  - Beat cards, contact sheets, film strips, approval cards, and consequence maps.
  - Clear authorship labels identifying the contributing skill.
  - Progressive disclosure for prompts, tokens, costs, and audit traces.
  - Motion to communicate handoffs, invalidation, and newly completed assets.

  Avoid:

  - A large prompt box as the primary interface.
  - Generic AI gradients, glowing orbs, and glass panels.
  - Raw chain-of-thought.
  - Fake agreement between specialists.
  - Indefinite loading spinners.
  - Dashboards dominated by technical metrics.
  - A generic node graph as the default user experience.

  ### 6.3 Skill Contributions

  Skill activity is displayed as concise production artifacts, not conversational transcripts.

  Examples:

  - Dash: creative direction card.
  - Kavi: hook and retention map.
  - Vidya: historical annotations.
  - Game designer: consequence map.
  - Reel: production feasibility report.
  - Fin: cost envelope.
  - Judge Panel: scored greenlight verdict.

  Users may expand a contribution to inspect its complete output and invocation metadata.

  ## 7. Runtime Architecture

  ### 7.1 Skill Invocation

  Application orchestration invokes skills through agentic-harness.

  For synchronous specialist judgment:

  agentic-harness/runtime/run_skill.py

  or:

  agentic-harness/runtime/agent.py::HarnessAgent

  The product orchestration layer coordinates multiple single-skill calls. Agentic-harness Layer B must remain narrow and must not be modified into a multi-agent framework.

  Each invocation records:

  - Skill name.
  - Skill version or content hash.
  - Resolved model.
  - Input and output tokens.
  - Duration.
  - Associated series and episode.
  - Associated production decision.
  - Resulting artifact.

  ### 7.2 Model Routing

  Project .harness/models.yaml controls model routing.

  Local defaults:

  cheap: ollama/qwen
  balanced: ollama/qwen
  frontier: ollama/qwen
  cheap-with-tools: ollama/qwen
  critic: ollama/qwen

  Cloud submission routing maps the required tiers to Qwen Cloud models.

  The project must verify exact Qwen model identifiers during implementation. Skills must not pin provider-specific models in their SKILL.md files.

  ### 7.3 ChronoCanvas Foundation

  Fork and reshape ChronoCanvas into this repository.

  Retain:

  - React, TypeScript, Vite, Tailwind, Zustand, React Query, and XYFlow.
  - FastAPI, async SQLAlchemy, PostgreSQL, Redis, ARQ, and LangGraph.
  - Existing Ollama provider support.
  - Story generation, scene editing, narration, video assembly, audit trails, and progress streaming.
  - Existing architecture invariants.

  Add:

  - Skill registry and skill-content loading.
  - Showrunner room orchestration.
  - Persistent series canon.
  - Skill contribution artifacts.
  - Approval and disagreement records.
  - Branch and consequence state.
  - Dependency-aware selective regeneration.
  - Qwen Cloud model routing.
  - Alibaba Cloud deployment.

  ### 7.4 Core Entities

  - Series
  - Character
  - Relationship
  - Canon fact
  - Story thread
  - Episode
  - Branch proposal
  - Beat
  - Shot
  - Audience choice
  - Canon mutation
  - Skill invocation
  - Skill contribution
  - Specialist disagreement
  - Approval gate
  - Production artifact

  Approved audience choices and canon mutations retain provenance and cannot be silently rewritten.

  ## 8. Public API Surface

  GET    /api/skills
  GET    /api/skills/{skill_name}

  POST   /api/series
  GET    /api/series
  GET    /api/series/{series_id}
  GET    /api/series/{series_id}/canon

  POST   /api/series/{series_id}/story-room
  GET    /api/episodes/{episode_id}/contributions
  GET    /api/episodes/{episode_id}/disagreements

  POST   /api/episodes/{episode_id}/greenlights/{gate}
  POST   /api/episodes/{episode_id}/produce
  POST   /api/episodes/{episode_id}/shots/{shot_id}/regenerate
  POST   /api/episodes/{episode_id}/finalize

  GET    /api/episodes/{episode_id}/choices
  POST   /api/episodes/{episode_id}/choices/{choice_id}/select

  GET    /api/episodes/{episode_id}/events
  GET    /api/episodes/{episode_id}/audit

  Redis pub/sub remains the only real-time backend channel.

  ## 9. Agentic-Harness Build Execution

  Claude must execute this PRD through agentic-harness.

  ### 9.1 Initialization

  git init
  ~/code/agentic-harness/bin/harness-init \
    --target=claude \
    --scope=build \
    --shape=sprint-iterative \
    --providers=ollama \
    --roster=custom
  bd init

  Run team-onboard and install project-owned forks of these existing skills:

  team-pm
  team-creative-director
  team-narrative-engineer
  team-historian
  team-game-designer
  team-line-producer
  team-ml-engineer
  team-cloud-economist
  team-frontend-engineer
  team-backend-engineer
  team-devops-engineer
  team-judge-panel
  pessimism

  Do not create replacement role skills.

  ### 9.2 Build Responsibilities

  Claude uses the same skills during implementation:

   Build concern                        Required skill
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━
   Product scope and sprint priority    team-pm
  ───────────────────────────────────  ─────────────────────────
   Product identity and UI direction    team-creative-director
  ───────────────────────────────────  ─────────────────────────
   Interactive branching behavior       team-game-designer
  ───────────────────────────────────  ─────────────────────────
   Narrative-state architecture         team-narrative-engineer
  ───────────────────────────────────  ─────────────────────────
   Historical-fiction trust model       team-historian
  ───────────────────────────────────  ─────────────────────────
   Production workflow feasibility      team-line-producer
  ───────────────────────────────────  ─────────────────────────
   Qwen routing and evaluation          team-ml-engineer
  ───────────────────────────────────  ─────────────────────────
   UI implementation                    team-frontend-engineer
  ───────────────────────────────────  ─────────────────────────
   Backend and persistence              team-backend-engineer
  ───────────────────────────────────  ─────────────────────────
   Cloud deployment                     team-devops-engineer
  ───────────────────────────────────  ─────────────────────────
   Cost controls                        team-cloud-economist
  ───────────────────────────────────  ─────────────────────────
   Sprint and submission review         team-judge-panel
  ───────────────────────────────────  ─────────────────────────
   Completion verification              pessimism

  Every P0 or P1 bead requires pessimism review before closure.

  ### 9.3 Build Sprints

  1. Harness And Foundation
      - Initialize harness and Beads.
      - Fork ChronoCanvas.
      - Onboard existing skills.
      - Establish Qwen/Ollama model routing.
      - Record significant differences from ChronoCanvas.

  2. Skill Runtime
      - Implement skill discovery, invocation, result persistence, contribution artifacts, and audit metadata.
      - Prove existing skills execute through Qwen on Ollama.

  3. Series Brain
      - Implement persistent canon, relationships, threads, episodes, branches, choices, and mutation provenance.

  4. Showrunner Rooms
      - Implement Story Room, Production Desk, Greenlight Council, disagreements, and approval gates.

  5. Episode Room UI
      - Build the room-based interface, preview stage, canon rail, beat board, timeline, and approval experience.

  6. Media Production
      - Connect approved plans to ChronoCanvas generation, selective regeneration, narration, and final assembly.

  7. Cloud And Submission
      - Add Qwen Cloud routing.
      - Deploy to Alibaba Cloud.
      - Create seeded demo series.
      - Record the public demo.
      - Run judge-panel and pessimism gates.

  ## 10. Acceptance Tests

  ### Skill System

  - Existing SKILL.md files are loaded without rewriting their role definitions.
  - Every displayed specialist contribution identifies its source skill.
  - Updating a project-local skill fork changes subsequent product behavior.
  - Skill invocations work through Qwen on Ollama.
  - Cloud mode records Qwen Cloud as the active provider.
  - No monolithic showrunner prompt exists.

  ### Team Workflow

  - Story Room invokes all required Story Room skills.
  - Production Desk invokes the appropriate production skills.
  - Greenlight Council blocks advancement until approval.
  - Disagreements remain visible.
  - User approval selects a decision without erasing dissenting recommendations.

  ### Product Workflow

  - Create a series.
  - Convene the Story Room.
  - Review and approve a branch.
  - Approve an episode plan.
  - Produce the episode.
  - Regenerate one shot without restarting production.
  - Approve the final cut.
  - Select the ending choice.
  - Verify canon changes affect the next episode.

  ### UI

  - A user identifies the active room and pending approval within ten seconds.
  - The interface remains understandable without reading chat logs.
  - The 9:16 episode remains visible during reviews.
  - Skill output appears as structured artifacts.
  - Generation latency is shown as concrete production activity.

  ### Submission

  - Public repository documents all post-May 26, 2026 work.
  - Qwen Cloud is load-bearing and visible in audit traces.
  - Backend deployment on Alibaba Cloud is demonstrated.
  - Demo video is under three minutes.
  - Judge Panel returns a passing verdict.
  - Pessimism review finds no unsupported completion claims.

  ## 11. MVP Exclusions

  - New role or persona definitions.
  - Public multi-user audience voting.
  - Real-time multiplayer collaboration.
  - Continuous conversational steering during playback.
  - Professional nonlinear video editing.
  - Automated social-media publishing.
  - Model fine-tuning.
  - Replacing agentic-harness with a custom multi-agent framework.

  ## 12. Locked Decisions

  - Existing Claude skills define all showrunner and build-team roles.
  - Skills are used in both the shipped product and the build workflow.
  - Showrunner specialists are organized into three visible rooms.
  - Qwen is the model runtime, not the role definition.
  - Local testing uses Ollama.
  - Hackathon deployment uses Qwen Cloud.
  - The product builds on a fork of ChronoCanvas.
  - The primary UI is an Episode Room, not chat.
  - The executable PRD lives at docs/PRD.md.