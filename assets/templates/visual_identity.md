# ChronoCanvas v2 — Visual Identity Guide

**Author:** Dash, Creative Director
**Date:** 2026-03-29
**Era:** Indian Subcontinent, 500–1200 CE
**Status:** Canonical. If it contradicts this doc, fix it.

---

## 1. The Creative Thesis

Every YouTube history channel about ancient India looks the same: overlit stock footage of temples, clip-art maps with swooshing arrows, the occasional AI image that screams "I was generated at 2am." They treat the visual layer as illustration — something to keep the eye busy while narration does the work. ChronoCanvas treats every frame as an argument. Our visual language fuses the dramatic tension of v1's noir grammar with the material warmth of Chola bronze, Chalukyan sandstone, and Ajanta mineral pigment — not because it looks pretty, but because this era's history was *forged in firelight and carved in stone*, and the images should feel that way. We don't illuminate history. We stage it.

---

## 2. Color Philosophy

### Primary Palette

These are the bones of every frame. At least two must be present in every composition.

| Name | Hex | OKLCH | Usage |
|------|-----|-------|-------|
| **Temple Stone** | `#B8956A` | `oklch(0.68 0.08 70)` | Architecture, ground planes, skin undertones. The default "surface" of v2. |
| **Chola Bronze** | `#8B5E3C` | `oklch(0.50 0.09 55)` | Figures, weapons, objects of power. Warm but heavy — carries authority. |
| **Lamp Black** | `#1A1612` | `oklch(0.15 0.02 60)` | Shadows, negative space. The one survivor from v1 noir, now warmer. Not blue-black. Brown-black, like soot. |
| **Monsoon Ivory** | `#F0E6D2` | `oklch(0.93 0.03 85)` | Highlights, sky wash, textile sheen. Replaces v1's cold white. Never pure #FFF. |

### Accent Palette

Used sparingly. If an accent color dominates a frame, something went wrong.

| Name | Hex | OKLCH | Usage |
|------|-----|-------|-------|
| **Ajanta Vermillion** | `#C0392B` | `oklch(0.52 0.17 25)` | Blood, kumkum, royal insignia, danger. The eye-puller. |
| **Pallava Teal** | `#1A6B5A` | `oklch(0.45 0.10 170)` | Water, copper patina, twilight sky. The cool counterweight. |
| **Turmeric Gold** | `#D4A017` | `oklch(0.73 0.14 85)` | Fabric, firelight halos, divinity markers. Earned, not sprinkled. |

### What We Keep from v1

- **Deep shadows as storytelling.** Noir gave us the habit of using darkness as meaning, not just absence of light. That stays. A figure stepping out of shadow still carries dramatic weight.
- **Limited palette per frame.** v1 rarely used more than 3 colors in a composition. That restraint is gold. Keep it.
- **High contrast at focal point.** The eye goes where the contrast is sharpest. v1 enforced this. v2 enforces it warmer.

### What We Reject

- **Blue-black shadows.** v1's noir shadows leaned cool and cinematic. Wrong for this era. Shadows here are warm — soot, char, deep umber. The darkest dark in any frame is brown, not blue.
- **Desaturated everything.** Noir loves draining color. This era was painted, dyed, gilded. We allow saturation where materials demand it — a vermillion tilak, a gold border on silk.
- **Grey skin tones.** The v1 palette made every face look like a Bogart still. South Asian skin rendered in warm light is gorgeous. Respect it.

> **Prompt note:** Always specify warm shadow tones ("deep umber shadows," "soot-dark background") and avoid "cinematic color grading" or "desaturated" in prompts. Explicitly call out skin warmth: "warm brown skin tones with golden highlights."

---

## 3. Lighting Language

Light is not decoration. It is the narrator's second voice.

### Interior Scenes (Temple Sanctums, Palace Courts)

**Primary source: oil lamps and shaft light.**

A sanctum lit by a single oil lamp creates a pool of warm gold that falls off fast into darkness. This is where v1's chiaroscuro earns its place — not as style, but as physics. Stone columns catch light on one face and go black on the other. Figures are half-revealed.

Palace courts get more ambient fill — multiple lamps, reflected light off polished stone floors — but never even illumination. There should always be a gradient. One side of the frame warmer, one cooler. One figure lit, one in silhouette.

Shaft light through stone windows or doorways is the prestige move. A blade of light cutting across a dark interior, catching dust motes, falling on a hand or a face. Use it for revelation moments.

> **Prompt note:** "Oil lamp lighting, single warm source, deep shadows on stone walls, volumetric dust in shaft light" — always specify the light source physically, never say "dramatic lighting" generically.

### Exterior Scenes (Battlefields, Trade Ports, Mountain Passes)

**Primary source: tropical sun, high and hard.**

The subcontinental sun between the tropics is not soft. It creates hard shadows under brows, under architectural overhangs, under elephant howdahs. Midday scenes should feel blinding at the top of frame and shadowed at ground level.

Trade ports and coastal scenes get the additional gift of water reflection — bounced light from below that opens up shadows on faces. This is the v2 equivalent of noir's "wet street" reflections.

Mountain passes (Deccan plateau, Western Ghats) get atmospheric haze — layers of depth created by humidity and distance. Foreground sharp, middle ground warm-hazed, background nearly silhouetted.

> **Prompt note:** "Hard tropical sunlight from above, deep shadows under architectural overhangs, warm atmospheric haze in background layers." For coastal: "reflected light from water surface filling shadows from below."

### Night / Dramatic Scenes

**This is where noir comes home.**

Night scenes and crisis moments get the full v1 treatment — but transposed warm. A war council by firelight. An assassination in a corridor lit by a single torch. A naval battle under monsoon clouds with lightning as the only illumination.

The key difference from v1: light sources are *visible* in frame. v1 noir used invisible, abstract light. v2 night scenes show the flame, the torch, the lightning bolt. The source is part of the composition.

> **Prompt note:** "Firelight illumination, visible flame source in frame, warm chiaroscuro, deep brown-black shadows." For storms: "monsoon clouds, lightning illumination, single flash freeze-frame."

---

## 4. Composition Principles

### Frame Layout

**Primary:** Modified rule of thirds, biased toward architectural symmetry.

This era built symmetrically — temples, courts, gopurams. Let the architecture provide the grid. Place the subject at the intersection of architectural lines, not arbitrary thirds. When there's no architecture, fall back to standard thirds.

**Secondary:** Depth layers. Every frame should have three readable planes:
1. **Foreground element** — a column, a weapon, a hand, a plant. Something that says "you are looking *through* something."
2. **Subject plane** — the figure or action.
3. **Background plane** — architecture, sky, crowd, landscape.

**Rejected:** Dutch angles. They were a v1 affectation. This era's visual grammar is grounded, monumental. Camera (conceptual camera) stays level. Tilt is earned — a collapsing structure, a body falling — not a default.

### Single Figures

Full or 3/4 body preferred over head-and-shoulders. These people wore elaborate clothing that tells you their caste, region, and era — cutting it off at the chest throws away information. Place the figure slightly off-center, with the larger space in the direction they're facing or acting toward.

### Crowds and Battles

**Don't try to render 10,000 soldiers.** AI can't do it well, and the attempt burns budget. Instead: 3–5 sharp foreground figures + a mass of suggested shapes in the mid-ground + dust/haze eating the background. Let the viewer's brain fill in scale.

### Architecture

Let it dominate. A Chola temple should dwarf the human figures. Shoot (conceptually) from below, looking up — the *bhakta's* perspective. Use architectural elements as natural framing devices: doorways, columns, carved lintels.

### Thumbnail Survival Test

Every frame must pass this: shrink it to 120x68 pixels. Can you still identify (a) a human figure, (b) an action or emotion, (c) a dominant color? If any of those three vanish, the composition is too subtle. Punch it up.

> **Prompt note:** "Subject placed at intersection of architectural lines, three clear depth planes, foreground framing element." For crowds: "3-5 detailed foreground warriors, suggested mass of figures in dusty mid-ground, haze-obscured background." Always include "clear readable silhouette" for thumbnail viability.

---

## 5. Texture & Material

### The Five Surfaces

Every scene in this era involves at most five dominant materials. Know how to render each:

**Stone** — Rough-hewn granite (Pallava, early Chola) or carved sandstone (Chalukya, Rashtrakuta). Never smooth. Always showing tool marks or weathering. The grain of the stone should be visible in close-ups. Warm grey-brown, never cold grey.

**Bronze** — The Chola Nataraja is the benchmark. Dark patina with golden highlights where the form catches light. Bronze should look *heavy*. It reflects light diffusely, not sharply — it's not chrome.

**Silk and Cotton** — Fabric drapes, it doesn't float. Kanchipuram silk has weight and sheen; cotton is matte and moves in wind. Fabric should show folds that obey gravity. The biggest AI tell is fabric that looks like it's underwater.

**Wood** — Teak, sandalwood. Dark, oiled, warm. Appears in ships, doors, furniture, weapons. It absorbs light rather than reflecting it. Grain visible.

**Water** — Rivers (Kaveri, Godavari, Narmada), the Indian Ocean, monsoon rain. Water is never pure blue in this context — it's brown-green in rivers, grey-teal in monsoon, deep blue-black at sea. Water reflects and distorts; use it for doubling compositions (a figure and its reflection).

### The Patina of Time

The goal is not "aged filter." It's specificity. A 10th-century bronze doesn't look like a 10th-century bronze because someone applied a grunge texture — it looks that way because copper oxidizes green in crevices while high points get polished by handling. A temple wall isn't "old-looking" — it has specific moss patterns where water channels down carved relief.

**The rule:** describe the *process* of aging in prompts, not the *effect*. "Moss growing in the carved recesses of sandstone relief" beats "ancient weathered temple" every time.

### What to Avoid: The AI Art Look

Three tells that scream "AI generated":
1. **Plastic skin.** Pores, texture, the slight unevenness of human skin. If a face looks like it's made of silicone, reject the image.
2. **Uniform lighting on textured surfaces.** Real stone in real light shows micro-shadows in every chip and groove. AI tends to flatten these. Push for "textured surface with visible grain and micro-shadows."
3. **Symmetry in natural objects.** Real faces, real trees, real fabric folds are asymmetric. If something looks too perfect, it probably is.

> **Prompt note:** Specify material physics: "rough-hewn granite with chisel marks and moss in recesses," "heavy silk with gravity-obeying drape folds," "dark bronze patina with golden highlights on raised surfaces." Always add "natural asymmetry, visible skin texture, micro-shadow detail on surfaces."

---

## 6. Typography & Title Cards

### Episode Title Treatment

**Energy:** Lapidary. Letters carved in stone, not printed on paper.

The title should feel like an inscription — strong, serifed, wide-set. Think of the Aihole inscription's authority. Not a decorative font. Not a "Sanskrit-looking" novelty font. A clean, high-contrast serif with generous letter-spacing, placed low in the frame (bottom third), left-aligned.

**Color:** Monsoon Ivory (`#F0E6D2`) with a subtle Turmeric Gold (`#D4A017`) inner glow or outline. Must read against both dark and medium-toned backgrounds.

**Never:** centered text floating over a busy composition, drop shadows, text outlines thicker than 2px, "ancient scroll" backgrounds behind text.

### Scene Transitions

**Primary transition: the hard cut.** Satyajit Ray didn't dissolve. We don't dissolve. Cut from composition to composition and trust the viewer.

**Exception:** Time passage. When we jump decades or centuries within an episode, use a brief **stone relief dissolve** — the live-action-style frame morphs into a carved stone relief version of itself (2–3 seconds), then cuts to the new scene. This is the signature v2 transition. It says: "what you just saw has become history."

**Rejected:** The v1 iris transition. It was noir-appropriate. It's not appropriate here.

### Text Overlays (Dates, Locations, Names)

Small, unobtrusive, bottom-left. Same Monsoon Ivory color. A thin horizontal rule above the text, extending about 30% of frame width. Font size: readable but not dominant. The image is the star, not the label.

For location names, include both the historical name and modern equivalent on first appearance: "Kanchi (Kanchipuram)." After that, use only the historical name.

> **Prompt note:** Title cards and text overlays are post-production composites, not AI-generated. However, when generating establishing shots intended for title card overlay, ensure the bottom third of the frame is relatively low-detail (dark stone, water, sky gradient) to support text readability.

---

## 7. Prompt Engineering Implications — Summary Table

| Visual Principle | Prompt Translation |
|---|---|
| Warm shadow palette | "Deep umber and soot-brown shadows, no blue-black, no cool tones in shadow areas" |
| Oil lamp interiors | "Single oil lamp warm light source, volumetric light, deep falloff to darkness" |
| Hard tropical sun | "Hard overhead tropical sunlight, deep shadows under overhangs, warm atmospheric haze" |
| Noir night scenes | "Visible fire/torch light source in frame, warm chiaroscuro, brown-black shadows" |
| Three depth planes | "Foreground framing element, sharp mid-ground subject, haze-softened background" |
| Bronze rendering | "Dark oxidized bronze patina, golden highlights on raised surfaces, heavy material weight" |
| Stone rendering | "Rough-hewn granite/sandstone, visible chisel marks, moss in carved recesses, micro-shadows" |
| Fabric rendering | "Heavy draped silk/cotton with gravity-obeying folds, natural creasing, matte or sheen per fabric type" |
| Anti-AI-look | "Natural asymmetry, visible skin pores and texture, micro-shadow detail on all surfaces" |
| Thumbnail viability | "Clear readable figure silhouette, dominant single color mood, high contrast at focal point" |
| Skin tone warmth | "Warm brown skin tones with golden highlights from light source, no grey desaturation" |
| Crowd scenes | "3-5 detailed foreground figures, suggested mass behind in dust/haze, avoid rendering individual faces in background" |
| Architecture scale | "Low camera angle looking up at temple/structure, human figures small against architecture" |
| Title card readiness | "Lower third of frame low-detail: dark ground, water, or sky gradient for text overlay space" |

---

## 8. Visual Signature Checklist

Before any frame ships, it must satisfy all five:

1. **Warm.** Is the dominant tone warm? Even night scenes should lean amber, not blue.
2. **Material.** Can you identify at least one real material (stone, bronze, silk, wood, water) by its rendered texture?
3. **Grounded.** Does the camera feel level and steady? Is the composition monumental, not tilted or frenetic?
4. **Lit with intent.** Can you point to the light source (real or implied)? Does the light reveal something about the story moment?
5. **Readable at thumbnail.** Shrink it. Does it survive?

If it fails any one, fix it before it enters the edit timeline.

---

*This document is the law until it isn't. When the frames start talking back — when the images teach us something we didn't plan for — we revise. But we revise from a position, not from drift. This is the position.*
