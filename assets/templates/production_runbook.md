# ChronoCanvas v2 — Production Runbook

**Author:** Amara, Technical Writer
**Date:** 2026-03-29
**Status:** Canonical. This is the operator guide for producing an episode.

---

## Prerequisites

Before starting any episode, ensure these are in place:

- [ ] Episode format definition reviewed (`assets/templates/episode_format.md`)
- [ ] Era research brief available (`assets/templates/era_research_brief.md`)
- [ ] Visual identity guide reviewed (`assets/templates/visual_identity.md`)
- [ ] Asset library directories exist (`assets/characters/`, `assets/environments/`, `assets/prompts/`)
- [ ] API keys configured: Gemini (story/narration), Imagen (images), Veo (video clips)
- [ ] Beads issue created for the episode and all sub-tasks

---

## Episode Production Pipeline

### Phase 1: Story Selection & Historical Brief
**Owner:** Kavi (narrative) + Vidya (history)
**Time budget:** 2-3 hours
**Cost budget:** ~$5-10 (LLM calls for research augmentation)

1. **Select story from candidates** in era research brief
   - Evaluate against hook strength, visual potential, asset reuse, series-building value
   - Kavi selects based on narrative drive; Vidya validates historical defensibility

2. **Produce historical brief for selected story**
   - Key events in chronological order
   - Named figures (limit to 3 for Episode 1, per format guide)
   - Specific visual anchors: sculptures, temples, artifacts that ground the imagery
   - Honest uncertainty flags (what we know vs. what we're inferring)

3. **Quality check:** Does the brief contain enough material for 7-8 minutes of narration without padding?

**Output:** `docs/episodes/ep{N}/historical_brief.md`

---

### Phase 2: Story & Episode Structure
**Owner:** Kavi (structure) + Vidya (fact-check)
**Time budget:** 3-4 hours
**Cost budget:** ~$10-15 (LLM story generation + iteration)

1. **Write the hook** (first 10 seconds)
   - Frame 1 visual concept (specific, not generic — per Visual Jolt spec in format guide)
   - Opening line (under 15 words, one of the five patterns from format guide)
   - Test: does this create a question the viewer needs answered?

2. **Build the beat sheet** using the episode format template
   - Map each structural beat (Context Drop → Character Intro → The Question → etc.)
   - Assign timestamp ranges
   - Identify The Turn (3:30-4:30) — this is non-negotiable, something must change here

3. **Write the cliffhanger** (last 30 seconds)
   - Select type from the Cliffhanger Taxonomy (Rank 1-5)
   - If this is not Episode 1, the cliffhanger must differ in type from the previous episode

4. **Draft narration script**
   - Follow narration voice guide: 8-15 word default sentences, fragments for emphasis
   - One new proper noun per 30 seconds maximum
   - Embed exposition in action, never in summary
   - Read aloud — if it drones, rewrite

5. **Quality check:** Retention checkpoint audit
   - 3-second cliff: Is the hook strong enough?
   - 30-second decision: Does the post-hook content deliver on the hook's promise?
   - 2-minute commitment: Is there narrative momentum without background dumps?
   - Mid-video dip (3:30-4:30): Is The Turn placed and strong?
   - End-card setup: Does the cliffhanger start at 7:15, not 7:45?

**Output:** `docs/episodes/ep{N}/beat_sheet.md`, `docs/episodes/ep{N}/narration_draft.md`

---

### Phase 3: Storyboard
**Owner:** Dash (creative direction) + Reel (rationalization)
**Time budget:** 2-3 hours
**Cost budget:** ~$5 (LLM assistance for scene descriptions)

1. **Scene breakdown**
   - One scene per structural beat from the beat sheet
   - Each scene: visual description, camera angle, lighting (per visual identity guide), duration
   - Identify which scenes reuse existing assets vs. need new generation

2. **Rationalize the storyboard** (Reel)
   - Flag scenes that exceed generation budget (too many new characters, complex crowds)
   - Suggest simplifications that preserve narrative intent
   - Apply the 3-attempt / 30-minute-per-clip constraint from PRD §9.3
   - Crowd scenes: 3-5 foreground figures + suggested mass (per visual identity §4)

3. **Dash reviews** visual coherence
   - Does every frame pass the Visual Signature Checklist (warm, material, grounded, lit with intent, thumbnail-readable)?
   - Are the five surfaces represented correctly (stone, bronze, silk/cotton, wood, water)?

**Output:** `docs/episodes/ep{N}/storyboard.md`

---

### Phase 4: Asset Generation
**Owner:** Suki (ML/image generation) + Dash (quality gate)
**Time budget:** 4-6 hours (the longest phase)
**Cost budget:** ~$15-25 (Imagen/Gemini calls — the bulk of per-episode cost)

1. **Check asset library first**
   - Before generating anything, search `assets/characters/` and `assets/environments/` for reusable assets
   - Episode 1 will have no reusable assets; Episodes 2+ should reuse 50%+

2. **Generate character assets**
   - Use prompt templates from visual identity guide §7
   - Always include: warm shadow tones, skin warmth, material specificity, natural asymmetry
   - Save canonical character prompts to `assets/characters/{era}_{name}_v1.md`
   - Maximum 3 named character designs per episode

3. **Generate environment assets**
   - Interiors: oil lamp lighting, single warm source, volumetric dust
   - Exteriors: hard tropical sun, atmospheric haze, three depth planes
   - Save to `assets/environments/{era}_{location}_v1.md`

4. **Generate scene images**
   - Work through storyboard scene-by-scene
   - Apply the "good enough" threshold: ≥80% quality, max 3 attempts per scene
   - If 3 attempts fail, simplify the scene (reduce characters, change angle, remove background complexity)

5. **Quality gate** (Dash)
   - Every frame against Visual Signature Checklist
   - Thumbnail survival test: shrink to 120x68px — can you see figure, action, dominant color?
   - Reject: plastic skin, uniform lighting on textured surfaces, unnatural symmetry

**Output:** Generated images in `output/episodes/ep{N}/`, asset files in `assets/`

---

### Phase 5: Narration Recording
**Owner:** Kavi (script finalization) + Suki (TTS generation)
**Time budget:** 1-2 hours
**Cost budget:** ~$3-5 (TTS API calls)

1. **Finalize narration script** based on actual generated visuals
   - Adjust timing to match scene durations
   - Ensure narration-to-visual sync (narration describes what's on screen, not what isn't)

2. **Generate voiceover**
   - Maintain consistent voice across episodes
   - Pacing: match the sentence rhythm patterns from format guide §6
   - Save voice config to `assets/narration/` for reuse

3. **Quality check:** Listen through once at 1x speed
   - Does it sound like a metronome? Rewrite.
   - Are fragment sentences landing as emphasis or as errors?
   - Is there dead air longer than 1.5 seconds without visual purpose?

**Output:** Audio files in `output/episodes/ep{N}/audio/`

---

### Phase 6: Edit & Assembly
**Owner:** Operator (manual for Episode 1)
**Time budget:** 3-4 hours
**Cost budget:** ~$0-5 (tool costs only)

1. **Assemble timeline**
   - Images + video clips matched to narration audio
   - Primary transition: hard cuts (per visual identity §6)
   - Time passage: stone relief dissolve (2-3 seconds)
   - No iris transitions, no dissolves except for time passage

2. **Add text overlays** (post-production composites, not AI-generated)
   - Title card: Monsoon Ivory serif, left-aligned, bottom third
   - Location/date labels: small, bottom-left, thin horizontal rule above
   - Historical name + modern equivalent on first appearance

3. **Add music/sound design**
   - Percussive, rhythmic, grounded — not cinematic-epic
   - Music enters at second 5-10, underneath narration
   - Silence or single sharp sound for Frame 1

4. **Quality check: full watchthrough**
   - Watch at 1x speed, no stopping
   - Note any moment where attention wanders — that's where viewers leave
   - Verify total runtime: 7-8 minutes target

**Output:** Final video file in `output/episodes/ep{N}/final/`

---

### Phase 7: Publishing Prep
**Owner:** Kenji (optimization) + Dash (thumbnail)
**Time budget:** 1-2 hours
**Cost budget:** ~$2-3

1. **Thumbnail**
   - Must be the strongest single frame from the episode
   - Must pass the 120x68px readability test
   - High contrast at focal point, clear subject, dominant color
   - Title text on thumbnail: 3-4 words maximum, high contrast

2. **Title**
   - Under 60 characters
   - Contains either a hook, a mystery, or a name the audience will recognize
   - No clickbait patterns ("You Won't Believe", "INSANE")

3. **Description & metadata**
   - First 2 lines: hook text (visible before "Show More")
   - Episode number and series name
   - Timestamps for key moments
   - Links to previous/next episode when available

4. **End screen setup**
   - Next episode tease: 3-5 seconds of visual from next episode
   - Subscribe prompt
   - Link to previous episode

**Output:** Thumbnail, title, description, tags, end screen assets

---

### Phase 8: Post-Mortem
**Owner:** Kenji (facilitator) + all team members
**Time budget:** 1 hour (immediately after publish)
**Cost budget:** $0

1. **Log actuals**
   - Total time per phase
   - Total cost per phase (API calls, compute, tools)
   - Implied hourly rate check: Total Cost = Cash Spend + (Hours × $50)

2. **Identify friction points**
   - What took longer than expected?
   - What required more than 3 attempts?
   - Where did grind labor dominate?

3. **Asset reuse inventory**
   - What new assets were created?
   - What can be reused in the next episode?
   - Update reuse counts in asset files

4. **Gate check** (at Gate episodes: 1, 3, 5)
   - Gate 1 (Episode 1): Total spend ≤ $150. Continue or redesign workflow?
   - Gate 2 (Episode 3): Total spend ≤ $400. Hard stop if views < 1K AND retention < 15% AND no improvement trend
   - Gate 3 (Episode 5): Total spend ≤ $700. Must show ≥30% reduction in cost and time per episode

5. **Analytics review** (delayed — revisit after 3-7 days)
   - Day 1-2 data: noisy, ignore
   - Day 3-7 data: directional, note trends
   - Week 2+ data: reliable, make decisions
   - Metrics: CTR (target >5%), retention (target >30%, minimum acceptable 15%)

**Output:** `docs/episodes/ep{N}/post_mortem.md`

---

## Episode Cost Target Reference

| Episode | Cash Budget | Target |
|---------|-----------|--------|
| 1 | $50-100 | Establish baseline |
| 2-3 | $30-60 | Each must be cheaper OR faster OR both |
| 4-5 | $20-40 | ≥30% reduction from Episode 1 |

---

## Kill Conditions (Stop Immediately If)

- Cost per episode is not decreasing
- Time per episode is not decreasing
- Retention stagnates or declines across 3+ episodes
- >70% of $1,000 CAD budget consumed with weak signals
- Grind labor dominates workflow (Flow < 50%)
- Burnout risk emerges

---

## Quick Reference: Tools & APIs

| Tool | Purpose | Cost Model |
|------|---------|-----------|
| Gemini | Story generation, research augmentation, narration drafting | Per-token |
| Imagen | Image generation (scenes, characters, environments) | Per-image |
| Veo | Video clip generation (motion scenes) | Per-clip |
| ComfyUI | Local video/image processing workflows | Compute cost |
| TTS API | Narration voiceover | Per-character |
| Video editor | Timeline assembly, transitions, text overlays | Tool license |

---

## Directory Structure Per Episode

```
docs/episodes/ep{N}/
  historical_brief.md
  beat_sheet.md
  narration_draft.md
  storyboard.md
  post_mortem.md

output/episodes/ep{N}/
  images/          # Generated scene images
  audio/           # Narration audio files
  video/           # Generated video clips
  final/           # Assembled final video
```

---

*This runbook is the operator manual. Follow it step by step for Episode 1. After the Episode 1 post-mortem, revise it based on what actually happened — not what we hoped would happen.*
