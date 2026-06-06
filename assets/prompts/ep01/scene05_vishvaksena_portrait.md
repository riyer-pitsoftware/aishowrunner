# Scene 5 — Vishvaksena Hero Portrait

**Type:** Character anchor
**Reused in:** Scenes 2, 7, 8, 9, 12, 13B (prompt block basis for all Vishvaksena scenes)
**Model:** FLUX.1 Dev FP8 + RealismLoRA
**Resolution:** 832x1216 (portrait)
**Steps:** 30 | CFG: 3.5 | Sampler: euler/simple

---

## Attempts

### v1 — Initial attempt
**Seed:** 3981131926
**LoRA strength:** 0.8
**Result:** Warm palette good, lean build correct, but forehead marks WRONG (red vertical tilak instead of white horizontal tripundra). Has beard/stubble. Image soft/blurry.
**Verdict:** REJECT — tripundra is non-negotiable

### v2 — Stronger tripundra language, no beard, sharper
**Seed:** 3041992331
**LoRA strength:** 0.9
**Result:** Clean-shaven fixed, but forehead still has red/white mix. Image very dark, face partially obscured.
**Verdict:** REJECT — too dark, tripundra still contaminated

### v3 — Portrait photography angle, explicit ash description
**Seed:** 1821720967
**LoRA strength:** 0.9
**Result:** Best tripundra (mostly horizontal white lines, small red element). Gorgeous warm amber palette, temple corridor setting. BUT has white beard despite negative prompt. Looks older than 52 (65+).
**Verdict:** BEST SO FAR — beard is the remaining issue

---

## Prompt — v2 (current best candidate)

```
Photorealistic portrait photograph of a South Indian Smarta Brahmin priest, 52 years old, lean and weathered. Clean-shaven face with no beard and no mustache. Dark brown skin with warm golden undertones.

FOREHEAD: Three perfectly horizontal lines of white sacred ash (vibhuti) painted across the entire width of his forehead. These are THREE PARALLEL HORIZONTAL WHITE LINES, not a dot, not a vertical mark, not red kumkum. Pure white ash lines on dark skin.

HEAD: Completely shaved bald head with a small grey topknot (shikha tuft) at the crown.

BODY: White cotton sacred thread (thin cord) crossing diagonally from left shoulder across bare chest to right hip. Rough dark-brown rudraksha seed bead necklace. Bare chest and arms showing lean, sinewy build. Plain white cotton dhoti wrapped around waist and legs.

POSE: Three-quarter profile facing right, standing upright with composed, watchful expression. Deep-set intelligent eyes looking slightly off-camera. Hands clasped at chest level.

SETTING: Standing in a dim stone temple interior. Single oil lamp light source from the upper left casting warm golden light on his face and chest, with deep umber-brown shadows on the right side. Rough-hewn sandstone pillar partially visible behind him. Warm atmospheric dust in the air.

STYLE: Sharp focus on face and upper body. Natural skin texture with visible pores. Warm color palette: Temple Stone amber, Chola Bronze brown, soot-black shadows. High contrast at focal point. Clear readable silhouette. Professional portrait photography, 85mm lens equivalent.
```

## Prompt — v3 (alternate angle)

```
Award-winning portrait photograph of an elderly South Indian Hindu priest, age 52, photographed in natural temple lighting. Sharp 85mm portrait lens, f/2.8, shallow depth of field.

The man has a completely shaved head with a tiny grey topknot at the crown. His forehead bears three wide horizontal stripes of white sacred ash — three bright white parallel horizontal bands spanning his full forehead width, the distinctive tripundra marking of a Shaiva devotee. NO red marks, NO dots, NO vertical lines — only horizontal white ash.

He is clean-shaven with NO facial hair whatsoever. His face shows deep character: pronounced cheekbones, deep-set watchful eyes, crow's feet, weathered dark brown skin with golden warmth. Natural skin texture, visible pores, asymmetric features.

Bare-chested, showing lean sinewy physique. A thin white cotton sacred thread crosses from his left shoulder diagonally across his chest. A strand of rough brown rudraksha seed beads hangs around his neck. He wears a simple white cotton dhoti.

He stands in three-quarter view in a stone temple corridor, turned slightly toward camera. Single source warm oil lamp light illuminates the left side of his face, casting the right side into deep warm brown shadow. Behind him: blurred sandstone pillars with carved relief, warm amber atmosphere, dust motes in air.

Color palette: amber, bronze, warm brown, ivory highlights. No cool tones anywhere.
```

## Negative Prompt (shared)

```
tilak, red forehead mark, vertical mark, dot, kumkum, sindoor, beard, mustache, goatee, facial hair, turban, hair on head, long hair, muscular build, fat, young, gold jewelry, weapons, modern clothing, blue shadows, cool tones, desaturated, grey skin, plastic skin, smooth skin, anime, cartoon, painting, illustration, blurry, soft focus, deformed, extra fingers, blue lighting, fantasy, CGI, 3D render
```

---

## Character Prompt Block (extract after approval)

Once the best portrait is selected, extract this reusable block for all Vishvaksena scenes:

```
[CHARACTER: VISHVAKSENA] South Indian Smarta Brahmin man, 52 years old, lean weathered build, dark brown skin with warm golden undertones, completely shaved head with small grey topknot (shikha), three horizontal white sacred ash lines (tripundra) across forehead, white cotton sacred thread crossing left shoulder over bare chest, rough dark-brown rudraksha bead necklace, plain white cotton dhoti, clean-shaven, no jewelry, no weapons. Expression: watchful, analytical, composed.
```

## Non-Negotiable Markers (fail the image if wrong)
- Three HORIZONTAL WHITE ash lines on forehead (not red, not vertical, not a dot)
- Shaved head (no hair except shikha topknot)
- Dark brown skin, warm tones
- Sacred thread visible
- White dhoti
- Clean-shaven (no beard, no mustache)
- Lean, older build
