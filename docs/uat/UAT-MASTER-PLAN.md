# UAT Master Plan — AI Showrunner

## 1. Scope

Acceptance of the AI Showrunner product against PRD §10 and the Qwen Cloud
Hackathon (Track 2) hard requirements. In scope: skill system, team workflow,
product workflow, UI, cost & budgeting, submission readiness. Out of scope (PRD
§11): multi-user voting, realtime multiplayer, NLE editing, auto social posting,
fine-tuning.

## 2. Entry criteria

- Target environment provisioned and migrated (`alembic upgrade head`).
- Build under test deployed (LOCAL or CLOUD) and reachable.
- Seed series available for product-flow suites (UAT-3).

## 3. Exit / acceptance criteria

- **100% of P0 cases pass on CLOUD.**
- No open Sev-1 defects.
- Master plan signed off (§6).
- Hackathon hard requirements (§5) each have a `pass` with evidence.

## 4. Traceability — PRD §10 → UAT

| PRD §10 acceptance criterion | UAT case(s) | Pri |
|---|---|---|
| SKILL.md loaded without rewriting roles | UAT-SKILL-001, 002 | P0 |
| Every contribution identifies its source skill | UAT-SKILL-003, UAT-UI-004 | P0 |
| Updating a project-local fork changes behavior | UAT-SKILL-004 | P0 |
| Skill invocations work through Qwen on Ollama | UAT-SKILL-005 | P0 |
| Cloud mode records Qwen Cloud as provider | UAT-SKILL-006, UAT-SUB-001 | P0 |
| No monolithic showrunner prompt exists | UAT-SKILL-007 | P1 |
| Story Room invokes all required skills | UAT-TEAM-001 | P0 |
| Production Desk invokes the production skills | UAT-TEAM-002 | P0 |
| Greenlight Council blocks advancement until approval | UAT-TEAM-003 | P0 |
| Disagreements remain visible | UAT-TEAM-004 | P0 |
| Approval keeps dissenting recommendations | UAT-TEAM-005 | P0 |
| Create a series | UAT-PROD-001 | P0 |
| Convene the Story Room | UAT-PROD-002 | P0 |
| Review and approve a branch | UAT-PROD-003 | P0 |
| Approve an episode plan | UAT-PROD-004 | P0 |
| Produce the episode | UAT-PROD-005 | P0 |
| Regenerate one shot without restarting | UAT-PROD-006 | P0 |
| Approve the final cut | UAT-PROD-007 | P0 |
| Select the ending choice | UAT-PROD-008 | P0 |
| Canon changes affect the next episode | UAT-PROD-009 | P0 |
| Identify active room + pending approval in 10s | UAT-UI-001 | P1 |
| Understandable without reading chat logs | UAT-UI-002 | P1 |
| 9:16 episode visible during reviews | UAT-UI-003 | P1 |
| Skill output appears as structured artifacts | UAT-UI-004 | P1 |
| Generation latency shown as production activity | UAT-UI-005 | P1 |
| Public repo documents post-2026-05-26 work | UAT-SUB-002 | P0 |
| Qwen Cloud load-bearing + visible in audit | UAT-SUB-001 | P0 |
| Alibaba Cloud deployment demonstrated | UAT-SUB-003 | P0 |
| Demo video under three minutes | UAT-SUB-004 | P0 |
| Judge Panel returns a passing verdict | UAT-SUB-005 | P1 |
| Pessimism finds no unsupported claims | UAT-SUB-006 | P1 |

## 5. Traceability — Hackathon hard requirements → UAT

| Requirement (memory/hackathon-facts) | UAT case | Pri |
|---|---|---|
| Qwen models on Qwen Cloud (load-bearing) | UAT-SUB-001 | P0 |
| Public OSS repo + detectable license | UAT-SUB-002 | P0 |
| Proof of Alibaba Cloud deployment | UAT-SUB-003 | P0 |
| Architecture diagram present | UAT-SUB-007 | P0 |
| Demo video ~3 min on YouTube/Vimeo/FB | UAT-SUB-004 | P0 |
| Track identified (AI Showrunner) | UAT-SUB-008 | P0 |
| Budget/cost controls credible (Qwen credits) | UAT-COST-001..006 | P1 |

## 6. Cross-cutting: cost & budgeting (TRD §6)

| Concern | UAT case |
|---|---|
| Every skill call metered + attributed | UAT-COST-001 |
| Every media job metered + priced | UAT-COST-002 |
| Pre-flight estimate at Episode Greenlight | UAT-COST-003 |
| Reserve→commit (no double-spend, no leak) | UAT-COST-004 |
| Hard cap blocks (`409 budget_exceeded`) | UAT-COST-005 |
| Soft cap warns (visible amber) | UAT-COST-006 |

## 7. Defect severities

- **Sev-1** blocks a P0 case or a hackathon hard requirement.
- **Sev-2** breaks a P1 case with no workaround.
- **Sev-3** cosmetic / minor.

## 8. Sign-off

| Suite | Cases | Pass | Fail | Blocked | Owner | Date | Status |
|---|---|---|---|---|---|---|---|
| UAT-1 Skill system | 7 | | | | | | ☐ |
| UAT-2 Team workflow | 5 | | | | | | ☐ |
| UAT-3 Product workflow | 9 | | | | | | ☐ |
| UAT-4 UI | 5 | | | | | | ☐ |
| UAT-5 Cost & budgeting | 6 | | | | | | ☐ |
| UAT-6 Submission | 8 | | | | | | ☐ |
| UAT-7 Sprint acceptance | per-sprint | | | | | | ☐ |

**Release acceptance:** ___________________  **Date:** __________
