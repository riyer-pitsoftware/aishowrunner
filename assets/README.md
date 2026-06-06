# ChronoCanvas Asset Library

> Replace regeneration with retrieval. Never recreate what can be reused.

## Structure

```
assets/
  characters/     # Character visual descriptions, canonical prompts, reference images
  environments/   # Location/setting prompts, architectural references
  prompts/        # Reusable prompt templates (Imagen, SDXL, Veo)
  workflows/      # ComfyUI workflow JSON files
  narration/      # Voice patterns, narration style guides, TTS configs
  templates/      # Episode structure templates, storyboard templates
```

## Naming Convention

`{era}_{subject}_{variant}.{ext}`

Examples:
- `characters/chola_rajendra_v1.md`
- `environments/thanjavur_temple_interior_v1.md`
- `prompts/imagen_temple_scene_v1.txt`
- `narration/charon_noir_style_v1.md`

## Usage

Each asset file should include:
1. **Description** — what this asset represents
2. **Era/Region** — when and where (for Vidya's validation)
3. **Prompt text** — the actual prompt or description (copy-pasteable)
4. **Source notes** — what historical evidence grounds this (sculptures, paintings, texts)
5. **Reuse count** — how many episodes have used this (updated manually)
