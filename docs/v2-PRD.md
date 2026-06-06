# ChronoCanvas Master PRD (v2)
## Self-Funded Narrative R&D Lab (Capital-Constrained System)

---

# 1. Purpose

ChronoCanvas is a:

> **Self-funded narrative production system where content output finances technical experimentation and system evolution**

It is NOT:
- purely a business
- purely a creative project
- purely a product build

It is:

> **A controlled experiment to validate whether episodic AI storytelling can become efficient, repeatable, and self-sustaining under strict constraints**

---

# 2. Core Operating Principle

Every action must improve at least one of:

- Cost efficiency
- Time efficiency
- Narrative retention

If it does not, it is eliminated.

---

# 3. System Model

ChronoCanvas operates as two parallel systems:

---

## System A — Production Factory

Purpose:
- Produce episodes
- Generate AdSense revenue
- Validate retention

---

## System B — R&D Lab

Purpose:
- Reduce friction
- Build reusable systems
- Improve workflow efficiency

---

## Governing Rule

> R&D must never block production

---

# 4. Hard Constraint: Budget

---

## Total Capital

> $1000 CAD (absolute, non-negotiable)

---

## Budget Philosophy

- Budget is used to **buy time and velocity**
- Not to minimize spend blindly
- Not to over-invest in tools

---

## Absolute Rules

- No additional funds beyond $1000 CAD
- No “one more tool” exceptions
- Budget exhaustion = experiment termination

---

## Budget Allocation (Initial)

| Category | Allocation |
|----------|-----------|
| LLM / API | $200 |
| Compute (GPU/tools) | $300 |
| Software/tools | $100 |
| Experiment buffer | $200 |
| Contingency | $200 |

---

# 5. Budget Governance

---

## Budget Gates

---

### Gate 1 — After Episode 1 (Max $150)

Evaluate:
- Total hours spent
- Cost breakdown
- Identified friction points
- Reusable assets

Decision:
- Continue or redesign workflow

---

### Gate 2 — After Episode 3 (Max $400)

#### Hard Stop Criteria

Stop if ALL are true:
- Views < 1,000 per episode
- Retention < 15%
- No improvement trend

---

### Gate 3 — After Episode 5 (Max $700)

Must demonstrate:
- ≥30% reduction in cost per episode
- ≥30% reduction in time per episode
- Asset reuse visible

---

### Final Gate — Remaining Budget (~$300)

Decision:
- Scale
- Stop
- Pivot

---

## Kill Conditions

Stop immediately if:

- Cost per episode is not decreasing
- Time per episode is not decreasing
- Retention stagnates or declines
- >70% budget consumed with weak signals
- Grind labor dominates workflow
- Burnout risk emerges

---

# 6. Time System

---

## Labor Types

---

### Grind Labor (Must Eliminate)

- Manual editing
- Frame fixing
- Repetitive operations
- Debugging pipelines excessively

---

### Flow Labor (Desired)

- System design
- Prompt engineering
- Pipeline improvements
- creative problem solving

---

## Target

> Flow ≥ 50% of total effort

---

## Rule

Optimize to eliminate **Grind**, not Flow

---

# 7. Episode 1 Rule

---

## Rule

> Do NOT automate before completing Episode 1 manually

---

## Purpose

- Establish baseline workflow
- Identify real bottlenecks
- Avoid premature optimization

---

# 8. Pipeline Architecture

---

## Core Flow

Idea  
→ Story Engine  
→ Storyboard Engine  
→ Asset Generation  
→ Edit  
→ Publish  
→ Analytics (Delayed)  
→ Optimization  

---

## Supporting Layer

- Cost Tracking
- Time Tracking
- Asset Library
- Backlog System

---

# 9. Core Components

---

## 9.1 Story Engine

Generates:
- Episodic structure
- Character arcs
- Cliffhangers

Focus:
- Continuation

---

## 9.2 Storyboard Engine

Outputs:
- Scene breakdown
- Visual prompts
- Shot sequence

Goal:
- Reduce ambiguity

---

## 9.3 Video Engine

Tools:
- Gemini (images)
- ComfyUI (video)
- Other APIs if needed

---

### Constraint: Good Enough Threshold

- Accept output at ≥80% quality
- Maximum 3 attempts per scene
- Maximum 30 minutes per clip

---

### Anti-Pattern

Spending hours refining one shot

---

## 9.4 Narration Engine

Purpose:
- Generate voiceover
- Maintain pacing

Constraint:
- Keep simple

---

## 9.5 Edit Engine

Goal:
- Assemble efficiently
- Avoid over-polishing

---

## 9.6 Publishing Engine

Handles:
- Title
- Thumbnail
- Metadata
- Upload

Goal:
- Maximize CTR and retention

---

## 9.7 Analytics Engine

Tracks:
- CTR
- Watch time
- Retention
- Drop-offs

---

### Analytics Delay Model

- Day 1–2: noisy
- Day 3–7: directional
- Week 2+: reliable

---

## 9.8 Cost Engine

Tracks:

- LLM cost
- Compute cost
- Tool cost
- Time spent

---

### Implied Hourly Rate

> Fixed at $50/hour

---

### Total Cost Formula

Total Cost = Cash Spend + (Hours × 50)

---

### Rule

Cost must decrease ≥20% per episode

---

## 9.9 Efficiency Engine

Tracks:

- Time reduction
- Cost reduction
- Asset reuse %
- Grind vs Flow ratio

---

# 10. Asset & Prompt Library (Core System)

---

## Purpose

> Replace regeneration with retrieval

---

## Assets to Store

- Character prompts
- Environment prompts
- Scene templates
- ComfyUI workflows
- Voice patterns
- Narrative structures

---

## Storage Structure

```

assets/
characters/
environments/
prompts/
workflows/
narration/

```

---

## Rule

> Never recreate what can be reused

---

## Goal

Scene generation becomes:
- CLI command OR
- One-click workflow

---

# 11. Technical Backlog System

---

## Purpose

Capture ideas without disrupting production

---

## Structure

Each item includes:
- Idea
- Problem
- Impact
- Priority

---

## Rule

> Backlog items can only be executed AFTER episode is published

---

# 12. Tinker Control System

---

## Rule

> 1 Tinker Day per Episode

---

## Definition

Time allowed for:
- pipeline improvements
- experiments
- automation

---

## Constraint

After Tinker Day → must ship

---

# 13. Narrative Strategy

---

## Rule

> Stay within ONE historical era for first 5 episodes

---

## Purpose

- Maximize asset reuse
- Reduce cost
- Improve efficiency

---

## Example

Focus:
- Roman Republic

Avoid:
- switching eras early

---

# 14. Hook Engine (Critical)

---

## Reality

> You have 1–2 seconds to capture attention

---

## Components

---

### Visual Jolt (Frame 1)

- High contrast
- Immediate tension
- Clear subject

---

### Audio Narrative Slap

- Conflict-driven opening
- No exposition
- Immediate stakes

---

## Rule

> If the hook fails, the entire episode fails

---

# 15. Episode Workflow

---

## Step 1 — Idea
Define hook and topic

---

## Step 2 — Story
Build narrative arc and cliffhanger

---

## Step 3 — Storyboard
Break into scenes

---

## Step 4 — Asset Generation
Create visuals and video

---

## Step 5 — Narration
Generate voiceover

---

## Step 6 — Edit
Assemble final output

---

## Step 7 — Publish
Upload and optimize

---

## Step 8 — Track
Log time, cost, metrics

---

## Step 9 — Analyze (Delayed)
Evaluate after 3–7 days

---

## Step 10 — Optimize
Update workflow

---

# 16. Parallel Pipeline Model

---

| Episode | Stage |
|--------|------|
| Ep1 | Published |
| Ep2 | Editing |
| Ep3 | Generation |
| Ep4 | Storyboarding |
| Ep5 | Idea |

---

## Purpose

Prevent idle time waiting for analytics

---

# 17. Metrics

---

## Production

- Time per episode
- Cost per episode

---

## System Health

- Flow ≥ 50%
- Grind decreasing

---

## Performance

- CTR > 5%
- Retention > 30%
- Minimum acceptable retention: 15%

---

## Financial

- Revenue per episode
- Cost vs revenue
- ROI trend

---

# 18. Cost Targets

---

| Episode | Cost |
|--------|------|
| 1 | $50–$100 |
| 2–3 | $30–$60 |
| 4–5 | $20–$40 |

---

## Rule

Each episode must be:
- cheaper OR
- faster OR
- both

---

# 19. Risks

---

## 1. Over-Engineering
Mitigation: Episode 1 manual rule

---

## 2. ComfyUI Time Sink
Mitigation: time caps and thresholds

---

## 3. Weak Hook
Mitigation: Hook Engine discipline

---

## 4. No Reuse
Mitigation: narrative clustering

---

## 5. Labor Explosion
Mitigation: hourly tracking

---

## 6. Burnout
Mitigation: flow optimization

---

# 20. Operating Principles

---

1. Ship first  
2. Systemize second  
3. Optimize third  

---

4. Track everything  
5. Enforce budget discipline  
6. Accept good enough  
7. Reuse aggressively  
8. Narrative > visuals  
9. Hook > everything  
10. Data is delayed  

---

# 21. Final Position

> ChronoCanvas is a capital-constrained narrative refinery that tests whether episodic AI storytelling can become efficient, repeatable, and self-sustaining.

---

# 22. Final Rule

> If it does not reduce cost, improve retention, or increase reuse — it is eliminated.

---

