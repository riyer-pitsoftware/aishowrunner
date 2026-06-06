# Phase 2 — Workflow Notes

## VRAM Profile (Task 2)

| Metric | Value |
|--------|-------|
| Peak VRAM (base workflow) | ___ GB |
| Peak VRAM (with RealismLoRA) | ___ GB |
| Idle VRAM (models loaded) | ___ GB |
| Headroom for Phase 3 InfiniteYou (~6GB FP8) | ___ GB |
| Text encoder offload needed? | yes / no |

Command: `nvidia-smi --query-gpu=memory.used,memory.total --format=csv`

## RealismLoRA Strength (Task 4)

| Strength | Skin texture | Lighting | AI smoothing? | Notes |
|----------|-------------|----------|---------------|-------|
| 0.4 | | | | |
| 0.6 | | | | |
| 0.8 | | | | |
| 1.0 | | | | |

**Chosen default:** ___
**Rationale:** ___

## Sampler Sweep (Task 5)

| Sampler | Steps | Scheduler | Time (s) | Quality notes |
|---------|-------|-----------|----------|---------------|
| euler | 20 | normal | | |
| euler | 25 | normal | | |
| euler | 30 | normal | | |
| dpmpp_2m | 25 | normal | | |
| dpmpp_2m | 25 | sgm_uniform | | |
| dpmpp_2m_sde | 25 | normal | | |
| dpmpp_2m_sde | 25 | sgm_uniform | | |

**Chosen combo:** ___
**Rationale:** ___

## Resolution Tests (Task 6)

| Resolution | Aspect | Use case | VRAM peak | OOM? | Quality |
|-----------|--------|----------|-----------|------|---------|
| 1024x1024 | 1:1 | Portraits | | | |
| 1024x768 | 4:3 | Interior scenes | | | |
| 1280x720 | 16:9 | Cinematic wide | | | |
| 768x1024 | 3:4 | Vertical portrait | | | |

## Quality Gate (Task 7)

| # | Subject | Pass? | Notes |
|---|---------|-------|-------|
| 1 | Indoor warm lighting | | |
| 2 | Outdoor harsh sun | | |
| 3 | Close-up 3/4 face | | |
| 4 | Medium shot with draped garment | | |
| 5 | Wide shot, pillared hall | | |

**Overall:** ___ / 5 pass (need 3/5)
