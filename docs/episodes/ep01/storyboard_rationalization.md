# Episode 1: "The Edict" — Storyboard Rationalization

**Season 1: THE MANYAKHETA GAME**
**Rationalized by:** Reel (Line Producer)
**Date:** 2026-03-29
**Status:** Production-ready assessment

---

> This document evaluates the 16-scene storyboard for production feasibility under the Episode 1 budget constraint ($50-100 total spend), identifies risks, proposes simplifications, and establishes the generation order. Every recommendation prioritizes shipping over polish.

---

## 1. Scene-by-Scene Feasibility

| # | Scene | Rating | Notes |
|---|-------|--------|-------|
| 1 | Copper Plate Close-up | **Moderate** | Photorealistic copper texture is achievable. The hands with sacred thread are the risk — AI regularly produces extra fingers or anatomically wrong hands. Mitigation: crop tight to fingertips only, keep hand area small in frame. Engraved Kannada script will likely be gibberish — acceptable if it reads as "ancient text" to a non-reader. The scratch/erasure detail is subtle enough that it may not survive generation; plan to accept "aged copper surface with marks" rather than a precise forensic scratch. |
| 2 | The Hook (Corridor) | **Easy** | Silhouetted figure in an architectural corridor is well within AI capability. Volumetric light through dust, laterite walls, deep shadows — these are strengths of current image models. No face detail needed. This is a safe scene. |
| 3 | Deccan Plateau Aerial | **Moderate** | Aerial/elevated landscape views are generally reliable. The risk is cultural specificity: Dravida-style temple towers in a Deccan landscape may drift toward generic "Indian temple" or Southeast Asian architecture. Prompt must anchor hard on "laterite," "stepped pyramidal shikhara," "dry brown plateau." The text overlay is post-production (added in edit), not part of the image generation — no risk there. |
| 4 | Boy King in Sabha-Mandapa | **Moderate** | Interior architectural scene with a small figure on a throne. Low angle is achievable. Risk: the courtier silhouette in foreground may merge with the main subject or disappear. The boy's age (13-14) is hard to control precisely — AI may produce a child or an adult. Mitigation: specify "adolescent, slim build" and accept reasonable range. Massive carved pillars are a strength for AI. |
| 5 | Vishvaksena Portrait | **Hard** | This is the HERO portrait — the character reference for 12+ scenes. Every cultural detail must be correct: tripundra, sacred thread placement, shaved head with shikha, rudraksha, kamandalu, panchakaccha dhoti. AI will struggle with: (a) the specific tripundra pattern (three horizontal ash lines, not a tilak dot), (b) sacred thread routing across bare chest, (c) the panchakaccha dhoti draping (tucked between legs — a very specific Indian garment fold). Expect 3 attempts minimum. This scene alone may consume 30 minutes. Worth it — this is the anchor for the entire season. |
| 6 | Basadi Approach | **Easy-Moderate** | Wide exterior with figures walking toward a building. AI handles this well. Guards with spears are moderate risk (weapon proportions can be wrong). The Jain basadi architecture needs prompt care to distinguish it from a Hindu temple — emphasize "modest, dressed stone, no gopuram." Harsh midday lighting is achievable. |
| 7 | The Threshold (Feet) | **Hard** | Bare feet at a threshold with a dead man's feet below is a very specific composition. AI struggles with: (a) feet anatomy, (b) specific spatial relationships between two sets of feet and a threshold stone, (c) the gold ankle rings on the corpse. This is a narrative-critical shot but may require significant prompt engineering. Simplification option: shift to a wider angle where feet are smaller in frame and the threshold framing is more prominent. |
| 8 | Reading the Body (Low Angle) | **Moderate** | Low angle looking up at a silhouetted figure in a doorway — achievable. The oil lamp at threshold edge is a nice detail AI can usually handle. Key: the camera MUST NOT show the body (we are looking UP from body level). This is actually easier because we are constraining what the AI needs to render. Risk: the "from the corpse's perspective" framing may confuse the model. Prompt as "low angle looking up at man standing in doorway, dramatic backlighting." |
| 9 | Missing Ring (Hands Close-up) | **Risky** | Two hands in close-up with specific details: (a) rings on three fingers but NOT the index finger, (b) a pale untanned band on the ringless finger, (c) one hand pointing at the other without touching, (d) sacred thread visible on the pointing hand. This is AI's worst nightmare. Hands with specific ring configurations are extremely unreliable. The "pale band where ring was removed" is a subtle skin-tone variation that image generators will almost certainly not produce correctly. **Recommend simplification** — see Section 4. |
| 10 | The Archives | **Easy** | Interior with warm single-light-source, figure sitting among documents. This is a classic "scholar by lamplight" composition that AI handles well. Copper plates and manuscripts are generic enough. The oil lamp warm pool effect is a strength. Low risk scene. |
| 11 | Oblique Light on Copper | **Moderate** | Close-up of copper plate with raking light. Similar to Scene 1 but with the "ghost text" requirement. The ghost text (previous text visible under erasure) is subtle — AI may or may not produce it. Mitigation: accept "aged copper plate surface with visible marks and scratches in dramatic side lighting." The Turmeric Gold highlight accent is achievable through prompt color guidance. This is a hero frame — worth 2-3 attempts. |
| 12 | Forged Name (Face, Uplit) | **Moderate** | Character portrait with dramatic uplighting. The uplight-from-below effect is achievable and dramatic. Risk: Vishvaksena's face must match the Scene 5 reference. AI consistency across scenes is the core challenge (see Section 2). Expression control ("recognition, not shock") is unreliable — accept reasonable dramatic expression. |
| 13A | Garuda Seal Close-up | **Moderate** | Close-up of a seal with specific iconography (Garuda). AI can produce a "mythological eagle-man seal on metal" but period-accurate Rashtrakuta Garuda style is unlikely. The scratches-on-ring forensic detail has the same problem as Scene 9 — too subtle. Accept "ornate seal with bird figure on aged metal." |
| 13B | Vishvaksena with Shadow | **Easy-Moderate** | Figure holding lamp in dark room with large shadow on wall. This is a classic dramatic composition. The enormous shadow effect is achievable with strong single-light-source prompting. The half-turn pose is moderate difficulty. |
| 14 | Basadi at Dusk | **Easy** | Same building as Scene 6 but at sunset. The warm palette shift (Vermillion/Gold sunset) is easy for AI. Silhouetted figure at threshold, palace in background. Wide shot reduces detail demands. Visual consistency with Scene 6 requires using the same prompt foundation with lighting changes. |
| 15 | Boy-King's Eyes | **Moderate** | Interior with two figures and lamp-lit pillars. The over-shoulder framing is achievable. Risk: Amoghavarsha's face must be young and match Scene 4. The "eyes looking directly at viewer" detail is a strength for AI portrait generation. Empty hall with repeating lamp-lit pillars is visually strong and achievable. |
| 16 | Cliffhanger (Copper Plate) | **Moderate** | Must echo Scene 1 precisely — same copper plate, same angle. This is a consistency challenge. If Scene 1's image is strong, Scene 16 can be generated using the same prompt with "face soft-focused behind the plate" added. Risk: the "bookend" visual match depends entirely on how good Scene 1 turns out. |
| 17 | End Card | **Easy** | Typography on dark background. This is a post-production/design task, not an AI image generation task. Zero risk. Build in Canva or any design tool. |

### Feasibility Summary

| Rating | Count | Scenes |
|--------|-------|--------|
| Easy | 4 | 2, 10, 14, 17 |
| Easy-Moderate | 2 | 6, 13B |
| Moderate | 7 | 1, 3, 4, 11, 12, 15, 16 |
| Hard | 2 | 5, 7 |
| Risky | 1 | 9 |

---

## 2. Character Consistency Plan

### The Core Problem

Vishvaksena appears in approximately 12 of 17 scenes. AI image generators have no built-in concept of character persistence. Every generation is independent. This is the single largest production risk for the episode.

### Strategy: Anchor Image + Prompt Template

**Step 1: Generate the Anchor Portrait (Scene 5)**

Scene 5 is the hero portrait. Generate this FIRST with maximum effort (3 attempts, 30 minutes). This establishes:
- Face structure, skin tone, age markers
- Sacred thread position and routing
- Tripundra style
- Body type and posture vocabulary

**Step 2: Build a Vishvaksena Prompt Block**

Once Scene 5 is approved, extract a reusable prompt block:

```
[CHARACTER: VISHVAKSENA] South Indian Brahmin man, approximately 55-60 years old,
lean build, dark brown skin weathered by sun, shaved head with small grey topknot
(shikha), three horizontal pale ash lines (tripundra) across forehead, white cotton
sacred thread (yajnopavita) crossing left shoulder over bare chest, plain white
cotton dhoti in panchakaccha draping, rough dark-brown rudraksha bead necklace,
no jewelry, no weapons. Expression: watchful, analytical, composed.
```

This block gets prepended to every scene prompt containing Vishvaksena. It will NOT produce perfect consistency, but it constrains the variation to an acceptable range.

**Step 3: Accept Controlled Variation**

Lock these details (non-negotiable, fail the image if wrong):
- Shaved head (no hair)
- Dark skin tone
- Tripundra on forehead (three horizontal lines)
- Sacred thread visible
- White dhoti
- Lean, older build

Allow these to vary (cheaper to accept than to fix):
- Exact facial features (nose shape, eye shape)
- Exact draping of dhoti
- Number/size of rudraksha beads
- Background details

### Amoghavarsha (2 scenes: 4 and 15)

Lower consistency pressure — only two scenes, different lighting conditions. Generate a simpler prompt block:

```
[CHARACTER: AMOGHAVARSHA] Indian adolescent boy, approximately 13-14 years old,
slim build, dark skin, fine white dhoti with gold-thread border, armlets,
single gold necklace, seated on carved stone throne. Expression: composed but uncertain.
```

### What NOT to Attempt

Do NOT try to use image-to-image or ControlNet-style consistency approaches for Episode 1. The PRD says "Do NOT automate before completing Episode 1 manually." If consistency proves too difficult with prompt-only approaches, that finding informs the R&D backlog for Episodes 2-5.

---

## 3. Asset Generation Order

### Phase 1 — Anchor Assets (Generate First, Sequentially)

These establish the visual vocabulary. Generate one at a time, approve before moving on.

| Priority | Scene | Asset | Why First |
|----------|-------|-------|-----------|
| 1 | **5** | Vishvaksena hero portrait | Character anchor for 12 scenes |
| 2 | **1** | Copper plate close-up | Recurring prop (Scenes 1, 11, 16) |
| 3 | **4** | Sabha-mandapa interior | Location reused in Scene 15 |
| 4 | **6** | Basadi exterior | Location reused in Scenes 7, 14 |

### Phase 2 — Dependent Scenes (Generate After Anchors, Parallelizable)

These use the anchor assets as prompt foundations.

| Batch | Scenes | Dependency |
|-------|--------|------------|
| A | 2, 3, 10 | Independent of character detail (silhouette, landscape, archive interior) |
| B | 8, 12, 13B | Depend on Vishvaksena anchor (Scene 5) |
| C | 11, 16 | Depend on copper plate anchor (Scene 1) |
| D | 7, 14 | Depend on basadi anchor (Scene 6) |
| E | 15 | Depends on sabha-mandapa anchor (Scene 4) + Amoghavarsha |

### Phase 3 — High-Risk Scenes (Generate Last)

| Scene | Risk | Strategy |
|-------|------|----------|
| 9 | Hands close-up | Generate last. If it fails after 3 attempts, use the simplified alternative (see Section 4). |
| 13A | Seal detail | Generate after Scene 9. Lower stakes — accept "ornate ancient seal" if period accuracy fails. |

### Phase 4 — Post-Production

| Asset | Tool |
|-------|------|
| 17 (End Card) | Design tool (Canva/Figma), not AI generation |
| Text overlays (Scenes 3, 5) | Added in video editor |
| Audio/narration | TTS, independent of image generation order |

---

## 4. Simplification Recommendations

### Scene 9 — The Missing Ring (RISKY -> Moderate)

**Problem:** Two hands in close-up with ring-specific details and subtle skin-tone variation.

**Simplification:** Widen the shot. Instead of an extreme close-up of two hands, make it a medium shot of Vishvaksena crouching near the body (body mostly out of frame), looking at the dead man's hand. The hand with missing ring is visible but smaller in frame, reducing the detail burden on the AI. The pointing gesture is replaced by Vishvaksena's gaze direction. The narration carries the forensic detail — the image just needs to show "investigator studying a dead man's hand."

**Narrative impact:** Minimal. The narration explicitly describes the missing ring. The viewer does not need to see the pale skin band at pixel level.

### Scene 7 — The Threshold (HARD -> Moderate)

**Problem:** Two sets of bare feet and a threshold stone in specific spatial relationship.

**Simplification:** Pull back to a medium shot from inside the basadi. Vishvaksena stands at the threshold, looking down. We see his full figure from the waist down, the threshold stone, and the edge of a draped cloth (suggesting the body) at the bottom of frame. Feet are smaller in frame and less anatomically demanding.

**Alternative:** Use a different angle entirely — shoot from the side, showing the threshold as a dividing line with Vishvaksena on one side and the shrouded form on the other. This is compositionally stronger AND easier to generate.

### Scene 5 — Vishvaksena Portrait (HARD but non-negotiable)

**No simplification possible.** This is the character anchor. Spend the full 30 minutes and 3 attempts here. If the panchakaccha draping is wrong, accept any "white draped garment" that reads as traditional Indian clothing. The sacred thread and tripundra are the non-negotiable identity markers.

### Hero Frames vs. Connective Tissue

**Hero Frames (worth extra attempts):**
- Scene 1 — Copper plate (opening image, thumbnail candidate, reused in 11 and 16)
- Scene 5 — Vishvaksena portrait (character anchor for entire season)
- Scene 11 — Oblique light forensic reveal (episode thesis image, thumbnail candidate)
- Scene 14 — Sunset silhouette (color palette showcase, thumbnail candidate)

**Connective Tissue (accept first good-enough result):**
- Scene 2 — Corridor silhouette (easy, atmospheric)
- Scene 3 — Aerial landscape (one attempt should suffice)
- Scene 6 — Basadi approach (straightforward wide shot)
- Scene 8 — Low angle doorway (standard dramatic composition)
- Scene 10 — Archive interior (classic single-light scene)
- Scene 13B — Shadow on wall (standard dramatic composition)
- Scene 15 — Over-shoulder throne room (moderate but not hero)
- Scene 17 — End card (design, not generation)

**Budget Implication:** Hero frames get 3 attempts each. Connective tissue gets 1-2 attempts. This is how we stay within budget.

---

## 5. Cost Estimate

### Image Generation (Imagen 3)

**Pricing assumption:** Imagen 3 via Vertex AI / AI Studio. Current pricing is approximately $0.04 per image at 1024x1024 (standard) or $0.08 at higher resolution. Using $0.04/image as the base estimate. Prices may vary with aspect ratio and quality settings.

| Category | Scenes | Attempts/Scene | Total Images | Cost/Image | Subtotal |
|----------|--------|----------------|-------------|------------|----------|
| Hero frames | 4 (1, 5, 11, 14) | 3 | 12 | $0.04 | $0.48 |
| Moderate scenes | 8 (3, 4, 7, 8, 12, 13A, 15, 16) | 2 | 16 | $0.04 | $0.64 |
| Easy scenes | 4 (2, 6, 10, 13B) | 1.5 avg | 6 | $0.04 | $0.24 |
| Scene 9 (risky) | 1 | 3 | 3 | $0.04 | $0.12 |
| **Subtotal** | **17 scenes** | | **37 images** | | **$1.48** |

**Buffer for additional iterations:** Assume 50% overshoot (prompt refinement, rejected outputs, variation experiments for character consistency).

| Item | Estimate |
|------|----------|
| Base image generation | $1.48 |
| 50% iteration buffer | $0.74 |
| **Total image generation** | **~$2.25** |

Image generation cost is trivially small. The real costs are elsewhere.

### Text Generation (Gemini)

Prompt engineering, scene descriptions, narration drafts, and iteration will consume Gemini tokens. Assuming Gemini 2.0 Flash for most work, with occasional Pro calls for quality:

| Task | Estimated Tokens (input+output) | Cost |
|------|------|------|
| Prompt engineering (16 scenes x ~2K tokens avg) | ~32K | ~$0.01 |
| Narration refinement | ~20K | ~$0.01 |
| Iteration/debugging | ~50K | ~$0.02 |
| **Total text generation** | **~100K tokens** | **~$0.04** |

### TTS Narration

~620 words of narration. Using Google Cloud TTS (WaveNet voices):

| Item | Estimate |
|------|----------|
| 620 words at ~4 characters/word = ~2,500 characters | |
| WaveNet pricing: $16/1M characters | $0.04 |
| Multiple takes (3x for pacing variation) | $0.12 |
| **Total TTS** | **~$0.15** |

### Video Clips (Veo 2)

If any scenes require video (slow push, camera movement), Veo 2 pricing applies. Current Veo 2 pricing is roughly $0.35/second of generated video.

| Scenario | Estimate |
|----------|----------|
| 0 video clips (images only, Ken Burns in editor) | $0.00 |
| 2-3 short clips (5s each) for key scenes | $5.25-$10.50 |

**Recommendation:** Do NOT use Veo 2 for Episode 1 unless the budget allows. Ken Burns (slow pan/zoom) on static images is the standard approach for this genre and costs $0. Save Veo 2 experimentation for the R&D backlog.

### Total Cost Estimate

| Line Item | Low | High |
|-----------|-----|------|
| Image generation (Imagen 3) | $2.25 | $4.00 |
| Text generation (Gemini) | $0.04 | $0.10 |
| TTS narration | $0.15 | $0.50 |
| Video clips (Veo 2) | $0.00 | $10.50 |
| Design tools (end card) | $0.00 | $0.00 |
| **Total API/cloud spend** | **$2.44** | **$15.10** |

### Budget Assessment

The API/cloud spend is well under the $50-100 target. The real cost of Episode 1 is labor time, not API calls. At the PRD's implied hourly rate of $50/hr:

| Task | Estimated Hours | Implied Cost |
|------|----------------|-------------|
| Prompt engineering + generation | 4-6 hrs | $200-300 |
| Narration recording/editing | 1-2 hrs | $50-100 |
| Video assembly/editing | 2-3 hrs | $100-150 |
| Quality review + fixes | 1-2 hrs | $50-100 |
| **Total** | **8-13 hrs** | **$400-650** |

**The constraint that matters is time, not money.** Image generation is cheap. The expensive part is prompt iteration, quality judgment, and assembly. The 30-minute-per-scene cap and 3-attempt limit are the real budget controls.

---

## 6. Prompt-Readiness Checklist

| Scene | Ready? | Additional Prompt Engineering Needed | Critical Negative Prompts |
|-------|--------|--------------------------------------|--------------------------|
| 1 | 85% | Need reference for Kannada script texture (accept decorative script). Specify exact crop and depth of field. | "no shiny copper, no modern elements, no blue tones, no text in English" |
| 2 | 90% | Straightforward. Specify laterite color precisely. | "no modern architecture, no blue sky, no green vegetation" |
| 3 | 75% | Need reference images of Dravida-style temple silhouettes to anchor the prompt. Specify "no lush green, no blue sky." | "no Mughal architecture, no Southeast Asian temples, no cool tones, no green landscape" |
| 4 | 80% | Specify Ellora/Pattadakal pillar proportions. Amoghavarsha age is tricky — test prompt wording. | "no ornate Mughal decoration, no gold throne, no painted walls" |
| 5 | 60% | **Heaviest prompt engineering.** Need to test tripundra rendering (many models default to tilak). Test sacred thread visibility. Test dhoti draping. Build iteratively. | "no tilak dot, no turban, no beard, no muscular build, no gold jewelry, no weapons, no modern clothing" |
| 6 | 80% | Specify Jain basadi vs Hindu temple distinctions. Guards need period-appropriate weapons. | "no Mughal style, no gopuram tower, no lush garden, no modern elements" |
| 7 | 65% | Composition is complex. Need to test threshold-framing with feet. Consider the simplified alternative first. | "no visible face on body, no blood, no gore, no modern flooring" |
| 8 | 80% | Low angle + silhouette is standard. Specify oil lamp type (clay diya). | "no modern lamp, no flashlight, no blue tones, no visible body/corpse" |
| 9 | 40% | **Needs major rework.** If attempting the original: build a very specific spatial prompt. If using simplified version: much more feasible. | "no extra fingers, no modern rings, no touching between hands" |
| 10 | 85% | Standard "scholar by lamplight." Specify copper plate stack appearance. | "no books, no paper, no modern shelving, no stone/marble floor" |
| 11 | 75% | Need to test raking-light effect on copper surface. The "ghost text" may require specific lighting angle language. | "no shiny copper, no direct overhead light, no blue tones" |
| 12 | 75% | Uplight portrait. Must match Scene 5 character. Test "lit from below by reflected warm light." | "no horror lighting, no cool blue uplighting, no skull-like shadows" |
| 13A | 70% | Garuda seal iconography needs reference. Accept stylized mythological eagle-man. | "no modern eagle, no heraldic eagle, no Western-style seal" |
| 13B | 80% | Standard dramatic single-light composition. Shadow-on-wall effect needs testing. | "no modern room, no electric light" |
| 14 | 85% | Sunset palette is well-supported by AI. Use Scene 6 prompt as base with time-of-day change. | "no cool tones in sky, no blue, no modern buildings in background" |
| 15 | 75% | Use Scene 4 prompt as base with lighting change (lamps instead of clerestory). Over-shoulder framing needs testing. | "no courtiers, no modern lamps, no ornate decoration" |
| 16 | 70% | Must visually echo Scene 1. Use Scene 1 prompt as base, add face element. | Same as Scene 1 |
| 17 | 95% | Design task, not prompt task. Minimal effort. | N/A |

### Scenes Requiring Pre-Generation Research

Before generating, gather visual reference images (from museum collections, archaeological photos) for:
- Rashtrakuta-period Garuda seal iconography (for Scene 13A)
- Panchakaccha dhoti draping (for Scene 5 prompt accuracy)
- 9th-century Deccan Jain basadi architecture (for Scenes 6, 7, 14)
- Ellora/Pattadakal pillar styles (for Scenes 4, 15)
- Copper plate grant examples (for Scenes 1, 11, 16 — actual museum photographs exist)

This reference gathering is a 30-60 minute research task that pays for itself in reduced generation iterations.

---

## 7. Reusable Asset Inventory

Every asset below is generated fresh for Episode 1 and reusable in Episodes 2-5.

### Character References

| Asset | Created In | Reusable In | Notes |
|-------|-----------|-------------|-------|
| Vishvaksena hero portrait | Scene 5 | Eps 2-5 (all) | Prompt block + approved reference image |
| Vishvaksena silhouette | Scene 2 | Any scene requiring distant/dark Vishvaksena | Low-detail version, flexible |
| Amoghavarsha on throne | Scene 4 | Eps 2-5 (court scenes) | Boy-king grows older across season — may need age-up |

### Location References

| Asset | Created In | Reusable In | Notes |
|-------|-----------|-------------|-------|
| Sabha-mandapa interior (day) | Scene 4 | Eps 2-5 (court scenes) | Core recurring location |
| Sabha-mandapa interior (evening) | Scene 15 | Eps 2-5 (night court scenes) | Same location, different lighting |
| Jain basadi exterior (day) | Scene 6 | Ep 2+ (if revisited) | Crime scene location |
| Jain basadi exterior (dusk) | Scene 14 | Ep 2+ | Same location, sunset palette |
| Akshapatala (archive) interior | Scene 10 | Eps 2-5 (investigation scenes) | Vishvaksena's workspace — high reuse |
| Laterite corridor | Scene 2 | Eps 2-5 (palace interiors) | Generic palace corridor |
| Manyakheta cityscape | Scene 3 | Eps 2-5 (establishing shots) | Capital city aerial |

### Prop References

| Asset | Created In | Reusable In | Notes |
|-------|-----------|-------------|-------|
| Copper plate (forged charter) | Scene 1 | Eps 2-5 (key evidence) | The central MacGuffin of the season |
| Copper plate (oblique light) | Scene 11 | Eps 2-5 (forensic scenes) | Variant of the same prop |
| Garuda seal | Scene 13A | Eps 2-5 (authentication scenes) | Royal seal — recurring symbol |
| Oil lamp (clay diya) | Scenes 8, 10, 12 | Eps 2-5 | Standard light source prop |

### Palette References

| Palette | Established In | Application |
|---------|---------------|-------------|
| Warm daytime (Temple Stone, Monsoon Ivory) | Scenes 1-8 | Default palette for all episodes |
| Archive lamplight (Chola Bronze, Lamp Black) | Scenes 10-13 | Investigation/research scenes |
| Sunset accent (Turmeric Gold, Ajanta Vermillion) | Scene 14 | Emotional climax moments |
| End card (Lamp Black, Monsoon Ivory) | Scene 17 | All episode end cards |

### Reuse Estimate for Episodes 2-5

| Episode | Estimated Reusable Assets from Ep1 | New Assets Needed | Savings |
|---------|-----------------------------------|-------------------|---------|
| Ep 2 | Vishvaksena, sabha-mandapa, archive, copper plate, palette | New characters, new locations (2-3) | ~40% fewer generations |
| Ep 3 | All Ep1 + Ep2 characters, most locations | 1-2 new locations | ~50% fewer generations |
| Ep 4-5 | Full character + location library | Minimal new assets | ~60% fewer generations |

This aligns with the PRD requirement: cost must decrease 20%+ per episode, and asset reuse is the primary mechanism.

---

## 8. Risk Register

### Risk 1: Character Inconsistency Across Scenes

**Probability:** High
**Impact:** High — Vishvaksena looking like a different person in every scene breaks viewer immersion.
**Mitigation:**
- Generate Scene 5 first as the anchor portrait.
- Build a strict prompt block reused across all scenes.
- Accept controlled variation in non-essential details (exact nose shape) while locking essential markers (tripundra, sacred thread, shaved head, skin tone, age).
- In editing, color-grade all Vishvaksena scenes to the same warm palette, which creates perceptual consistency even when faces vary slightly.
- If consistency is still unacceptable after Episode 1, add image-to-image reference workflow to the R&D backlog for Episode 2.

### Risk 2: Hands and Feet Anatomy Failures

**Probability:** High (near certain for close-ups)
**Impact:** Medium — Scenes 1, 7, 9, 16 all feature hands or feet prominently.
**Mitigation:**
- Scene 1: Crop to fingertips only, keep hand area to <15% of frame.
- Scene 7: Use the simplified wider-angle alternative.
- Scene 9: Use the simplified medium-shot alternative. The narration carries the forensic detail.
- Scene 16: Same approach as Scene 1.
- General rule: never put hands in the center of a hero frame. Push them to edges or partial crop.

### Risk 3: Cultural Detail Inaccuracy

**Probability:** Medium-High
**Impact:** Medium — Incorrect architectural style, wrong religious iconography, or anachronistic elements undermine the "grounded history" promise.
**Mitigation:**
- Pre-generation reference research (30-60 min investment).
- Strong negative prompts ("no Mughal architecture, no Southeast Asian style").
- Accept "generically correct Indian medieval" where period-specific accuracy is impossible for the AI to achieve. The narration provides the specificity; the image provides the atmosphere.
- Vidya (Historian) reviews generated images for dealbreakers before assembly.
- Flag known weaknesses: tripundra vs tilak, Jain basadi vs Hindu temple, Dravida vs Nagara architecture.

### Risk 4: Time Overrun on Prompt Engineering

**Probability:** Medium
**Impact:** High — The 30-minute-per-scene cap is the real budget control. If Scene 5 alone takes 2 hours of prompt iteration, the entire schedule collapses.
**Mitigation:**
- Strict timer discipline. Set a 30-minute alarm per scene.
- After 3 attempts, accept the best result and move on. "Good enough" is the operating principle.
- Generate easy scenes first (after anchors) to build momentum and calibrate expectations.
- Document every successful prompt pattern immediately — this is the prompt library for Episodes 2-5.

### Risk 5: Scope Creep from Storyboard Ambition

**Probability:** Medium
**Impact:** Medium — The storyboard is cinematically ambitious (specific camera angles, forensic details, visual bookends). The gap between storyboard intent and AI output may tempt endless iteration.
**Mitigation:**
- This rationalization document IS the scope control. The simplified alternatives in Section 4 are pre-approved fallbacks.
- The editor (assembly phase) can compensate for individual frame weakness through pacing, narration timing, and Ken Burns movement.
- Principle: the narration carries the story. The images support the narration. If the image is 70% of the storyboard intent but the narration is 100%, the scene works.

---

## 9. Production Schedule (Recommended)

| Phase | Duration | Scenes | Notes |
|-------|----------|--------|-------|
| **Research** | 0.5-1 hr | — | Gather visual references for architecture, costumes, copper plates |
| **Anchor Generation** | 2-3 hrs | 5, 1, 4, 6 | Sequential. Scene 5 gets full 30 min. Others 20 min each. |
| **Batch Generation** | 2-3 hrs | All remaining | Parallel batches per Section 3. Easy scenes first. |
| **Risky Scenes** | 0.5-1 hr | 9, 13A | Last. Use simplified versions if needed. |
| **Narration** | 1-1.5 hrs | All | TTS generation + pacing review |
| **Assembly** | 2-3 hrs | All | Ken Burns, timing, transitions, audio mix |
| **Review + Fix** | 1 hr | — | Final pass, replace any dealbreaker frames |
| **Total** | **9-13 hrs** | | Fits within PRD Episode 1 expectations |

---

## 10. Go/No-Go Recommendation

**GO.** The storyboard is ambitious but achievable within constraints, provided:

1. Scene 5 (Vishvaksena portrait) is treated as the critical-path anchor and generated first with full effort.
2. Scenes 7 and 9 use the simplified alternatives described in Section 4.
3. No Veo 2 video clips are attempted — Ken Burns on static images for Episode 1.
4. The 30-minute-per-scene cap and 3-attempt limit are enforced without exception.
5. The narration is trusted to carry forensic detail that images cannot render (pale ring band, ghost text, specific religious marks).

The API cost is negligible ($2-15). The time cost (9-13 hours) is the real investment. This is consistent with the PRD's Episode 1 manual baseline philosophy — the goal is to discover the bottlenecks, not to optimize prematurely.

**Assets generated here will pay for themselves across Episodes 2-5.** The character references, location references, prompt blocks, and palette definitions are the foundation of the season's asset library. Episode 1 is expensive in time because everything is new. Episode 2 should be 40% faster.
