# Generation package v2 — four cinematic clips for «RETURN TO THE SLOPE»

Ready-to-use package for genuine external AI video generation. Everything here is a
**new file**; no approved asset, no final render, no earlier package was modified.

## Read in this order

| # | File | What it is |
|---|---|---|
| 1 | [`prompts/clip_A_fall.md`](prompts/clip_A_fall.md) | Prompt A — fall, slide, lying frightened |
| 2 | [`prompts/clip_B_rescue.md`](prompts/clip_B_rescue.md) | Prompt B — rescue, assessment, stretcher transport |
| 3 | [`prompts/clip_C_rehab.md`](prompts/clip_C_rehab.md) | Prompt C — assessment, hard early movement, support, progress |
| 4 | [`prompts/clip_D_return.md`](prompts/clip_D_return.md) | Prompt D — confident return to the Altai slopes |
| 5 | [`02_reference_image_guide.md`](02_reference_image_guide.md) | Which approved image accompanies which prompt |
| 6 | [`03_continuity_guide.md`](03_continuity_guide.md) | Face, wardrobe, equipment, center identity, grade, hard rejects |
| 7 | [`04_technical_guide.md`](04_technical_guide.md) | Download the MP4s, name them, place them, verify them |
| 8 | [`05_vo_mapping.md`](05_vo_mapping.md) | Clip → approved Russian VO → 77-second timeline |
| 9 | [`06_brand_copy_postproduction.md`](06_brand_copy_postproduction.md) | The exact brand copy and how it is typeset |
| 10 | [`prompts_export_v2.json`](prompts_export_v2.json) | The same four prompts, machine-readable |

Helpers (new, non-destructive):

```bash
.venv/bin/python video/tools/stage_clip_references.py   # copy refs for upload, hash-verified
.venv/bin/python video/tools/check_hero_clips.py        # inspect the four downloaded MP4s
.venv/bin/python video/tools/assemble_hero_clips.py --force   # ONLY when clips are accepted
```

## At a glance

| Clip | Beat | Slot | Requested length | Produces real motion |
|---|---|---|---|---|
| A | carve → loss of grip → fall → slide → frightened | 00:00–00:11 | 10–12 s | yes, if a video model is used |
| B | approach → assess → stabilise → sled down | 00:11–00:19 | 8–10 s | yes |
| C | assessment → hard movement → support → teamwork | 00:24–00:36 | 10–12 s | yes |
| D | return → two clean carved turns → opens out | 01:02–01:12 | 10–12 s | yes |

Target: **39 s of genuine motion inside the 77 s film**; the rest stays on approved
stills with eased reframes, and the approved 70.16 s voice-over is carried unchanged.

## Two things to approve before the final cut

1. **Clip B adds a rescue beat** the locked v2 edit does not have. It sits exactly over
   «После падения — тишина и вопрос», but it does displace the aftermath hold and shortens
   the exterior push. See `05_vo_mapping.md` § "needs owner sign-off".
2. **Rescue personnel are new content** — no approved reference exists for them. They are
   specified as unbranded mountain ski-patrol, not center staff, and must be reviewed
   on the first accepted take.

## Guardrails baked into every prompt

No generated text, subtitles, logos, signage, watermarks or end cards · no cuts or
camera jumps inside a clip · no body morphing, duplicated or extra limbs · no
impossible physics · no graphic injury, blood, diagnosis or outcome claim · the patient
never walks after the fall · the action axis (upper right → lower left, camera on the
downhill front-quarter) is never mirrored · the center's room and building are never
redesigned.
