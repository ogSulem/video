# RETURN TO THE SLOPE

Production workspace for a premium cinematic commercial for a sports rehabilitation center in the Altai Mountains, Russia.

## Current status — 2026-10-28

**v3 is the current master:** [`video/final/altai_rehabilitation_v3.mp4`](video/final/altai_rehabilitation_v3.mp4)
— 78.79 s, 1 891 frames, 1920 × 1080, 24 fps, H.264 High, AAC-LC stereo;
measured −16.4 LUFS / −1.0 dBTP, 0 duplicate frames. SHA-256
`2e9ef1c0bbfd8d26ec865c5448beebe7818fe925dce1beb5dfe9aac9263b997a`.

V3 is the first cut that uses the generated footage. The three clips in the
repository root (`scene a1.mp4`, `scene a2.mp4`, `scene d.mp4` — carve, fall,
return; 26.1 s of genuine generated motion) are re-timed to 24 fps with
per-frame optical flow, so they carry **32.5 s (41 %)** of the film in cinematic
slow motion and speed ramps with no duplicated frames. The approved stills
supply the middle of the film as **staged living stills** — depth-layered
parallax, a focus pull and atmosphere, authored at four key images per second
and interpolated to full frame rate — and are labelled as stills, never passed
off as footage. The end card is typeset in post from the owner-approved copy.

The locked Russian narration is byte-identical to the approved file and starts
the picture. Two mix-only operations are applied to an in-memory placement copy
and are switchable off: repair of four codec clicks inside the MP3, and a
broadcast voice curve (the delivered reading is heavy below 120 Hz and light
between 1 and 3.4 kHz). The picture is cut to the narration at phrase
boundaries recovered from the audio itself. The original score and sound design
are synthesised locally; the mix is measured to −16 LUFS.

Full detail: [`video/README.md`](video/README.md) ·
[design and provenance notes (RU)](production/v3_design_notes.md) ·
[QC report](video/tests/V3_QC_REPORT.md) · shot/loudness manifest
[`video/final/altai_rehabilitation_v3.json`](video/final/altai_rehabilitation_v3.json).

**Preserved history:** the 77-second v2 review render
([`video/final/altai_rehabilitation_commercial_v2.mp4`](video/final/altai_rehabilitation_commercial_v2.mp4)),
the v1 baseline, the six-second motion capability test
([`video/tests/skier_motion_test_v1.mp4`](video/tests/skier_motion_test_v1.mp4))
and their QC records. The approved reference set (REF-ARC-01, REF-CHAR-01,
REF-INT-01/02, REF-SCENE-01…10) and the VO script/audio are unchanged; every
hash is pinned in `video/filmkit/sources.py` and re-checked before each render.

## What is still open

- **Owner approval** of the v3 cut, the mix, the staged stills and the drawn
  end-card mark (no official logo file was ever supplied; the mark is
  decorative and is not presented as a logo).
- **Factual, clinical/legal and rights review** before any public release.
  Nothing in the film asserts a guaranteed return, a diagnosis, a named device
  or a service the centre has not confirmed.
- **Source-quality limits that cannot be fixed in the edit:** the clips are
  1280 × 704 / 1344 × 768 and are upscaled to 1080p; AI artefacts in the fall
  (skis, gloves) are softened by slow motion but not removed; the skier in the
  clips and the athlete in the interiors are different people and cannot be
  reconciled without new generation.
- A separately composed 9:16 social version (not a blind centre crop) has not
  been built in this pass.

## Production documents

- [Creative brief](production/creative_brief.md)
- [Visual style guide](production/visual_style_guide.md)
- [Master script](production/master_script.md)
- [Shot list](production/shot_list.md)
- [Continuity guide](production/continuity_guide.md)
- [Approval workflow and asset manifest](production/asset_manifest.md)
- [v3 design and provenance notes (RU)](production/v3_design_notes.md)
- [Architecture prompt brief](prompts/architecture.md), [character brief](prompts/character.md), [interior/equipment brief](prompts/interiors.md)
- [Voice-over and sound design](editing/voiceover.md), [v2 sound design](editing/sound_design.md), [v2 edit notes](editing/edit_notes.md), [director's assembly plan](editing/video_assembly_plan.md)
- [Reproducible v3 renderer](video/README.md) and [v3 QC report](video/tests/V3_QC_REPORT.md)

## Factual advertising safeguard

Before public release, verify the center's existence and name, actual
services/equipment, staff credentials, website/domain, rights, clinical wording,
and all implied outcomes. Do not present proposed capabilities as available
facts or imply a guaranteed return.
