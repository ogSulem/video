# Altai rehabilitation commercial — v3

## Deliverables

- **Current master:** [`final/altai_rehabilitation_v3.mp4`](final/altai_rehabilitation_v3.mp4)
  — 78.79 s (1 891 frames), 1920 × 1080, 24 fps, H.264 High / yuv420p / BT.709,
  AAC-LC stereo 48 kHz 192 kb/s, H.264 at ~6.3 Mbit/s. Measured: **−16.4 LUFS integrated, 6.2 LU
  range, −1.0 dBTP**. SHA-256 `2e9ef1c0bbfd8d26ec865c5448beebe7818fe925dce1beb5dfe9aac9263b997a`.
  Sidecar manifest with every pin, shot and loudness figure:
  [`final/altai_rehabilitation_v3.json`](final/altai_rehabilitation_v3.json).
- **QC record:** [`tests/V3_QC_REPORT.md`](tests/V3_QC_REPORT.md).
- **Earlier review masters, preserved:** [`final/altai_rehabilitation_commercial_v2.mp4`](final/altai_rehabilitation_commercial_v2.mp4)
  and [`final/altai_rehabilitation_commercial_v1.mp4`](final/altai_rehabilitation_commercial_v1.mp4).
- **Capability test, preserved:** [`tests/skier_motion_test_v1.mp4`](tests/skier_motion_test_v1.mp4).

## What is new in v3

V2 was built from stills moved by a 2D crop: no depth, no atmosphere, no
articulated motion. V3 adds the three things that were missing, all locally and
deterministically, and it is the first cut that uses the generated clips.

| | v2 | v3 |
|---|---|---|
| Genuine motion footage | none | **32.5 s (41 %)** from the three generated clips |
| Still shots | flat crop | depth-layered parallax, focus pull, atmosphere |
| New image per frame | no | yes — key images at 4/s, interpolated to 24 fps; **0 duplicate frames in 1 891** |
| Cut to the narration | approximate | sentence-level, recovered from the audio |
| Mix | synthetic bed | calibrated score + design, −16 LUFS / −1.5 dBTP |
| End card | typeset | typeset, with a drawn mark and a staged reveal |

### 1. The three clips are re-timed, not padded

`scene a1.mp4` (carve), `scene a2.mp4` (fall, then lying in the snow) and
`scene d.mp4` (return, camera tilting into the sky) are 26.1 s of genuine
generated footage. V3 re-times them into 24 fps with per-frame optical-flow
interpolation — slow motion and speed ramps — so the same footage carries
**32.5 s** of screen time with **no duplicated frame**. Measured mean
frame-to-frame difference on a retimed section: 8.24, against 5.02 for a
duplicate-frame version of the same section.

### 2. The approved stills are staged, not slid

Each interior still becomes a depth-layered camera move: a smooth depth proxy
(floor near, wall and glass far), a near layer that travels and scales more than
the far layer, a focus pull that softens the far layer over the shot, plus
falling snow, a slow exposure breath and sub-pixel operator drift. The class is
deterministic — `render(t)` depends only on `t`.

Key images are authored at 4 per second and the same flow engine fills the gap
to 24 fps, so every delivered frame is a new image rather than a repeat.

### 3. Honest provenance

| | Screen time | Share |
|---|---|---|
| Generated motion footage (3 clips, re-timed) | 32.5 s | 41 % |
| Approved stills, staged as living stills — **not** footage | 40.3 s | 51 % |
| Typeset brand card | 7.6 s | 8 % |

The film contains no generated text, no logo, no invented equipment and no
medical claim. The card carries only the owner-approved copy
(`РЕАБИЛИТАЦИОННЫЙ ЦЕНТР АЛТАЙ`, `Твой сезон продолжается.`,
`altaysportreab.ru`); the mark above it is a drawn decorative line, not a logo.

### 4. The narration is untouched

`audio/voiceover/voiceover_ru_full_v1.mp3` is opened read-only, hash-pinned and
used from its start; it is never re-timed, re-worded or re-rendered. The picture
is cut to it — phrase boundaries were recovered from the audio itself (pause
detection fitted to syllable counts, 235 ms per syllable, fit error under 0.1 s).

Two mix-only operations are applied to an **in-memory placement copy**, and
both are switchable off:

* **codec-artefact repair** — the delivered MP3 contains a codec click at
  22.89 s (13 samples) and three smaller ones at 27.73 / 49.89 / 56.05 s. They
  are interpolated out of the placement copy. The source file remains
  byte-identical. `--no-declick` leaves them in.
* **broadcast voice curve** — the delivered reading is heavy below 120 Hz and
  light in the intelligibility band (measured: −0.9 dB under 120 Hz, −20.7 dB
  between 1 and 3.4 kHz). The placement copy gets a presence lift and a rumble
  cut, with the peak held where it was. `--no-vo-eq` bypasses it.

### 5. Original score and design

Synthesised locally — warm detuned pads, a felt-piano figure, a restrained sub
pulse, a synthetic stereo reverb — plus alpine wind, ski edge on cold snow, one
soft snow impact, air on the transitions and two breath cues. The bed is
calibrated against the narration (music sits 9 LU under the voice in the gaps),
ducked 7.5 dB under speech, and the whole mix is normalised to −16 LUFS with a
−1.5 dBTP ceiling in two measured passes.

## Reproduce

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r video/requirements.txt
.venv/bin/python video/render_film_v3.py --verify-only     # pins + full shot plan
.venv/bin/python video/render_film_v3.py --preview 44 52   # 8 s silent proof
.venv/bin/python video/render_film_v3.py --force           # full master
```

The renderer verifies every source hash before the first frame, renders the
score first (so an audio problem fails in seconds instead of after the picture),
then encodes 1 891 frames through x264 `medium` / CRF 17 and muxes the mix.

Useful switches: `--no-declick`, `--no-vo-eq`, `--crf`, `--preset`,
`--out PATH`, `--force`.

## File map

```
video/
  render_film_v3.py           v3 renderer: picture, score, mix, master, manifest
  filmkit/
    sources.py                hash-pinned read-only access to approved material
    motion.py                 optical-flow retiming and key-image interpolation
    staging.py                depth proxy, layered camera, living stills, snow
    look.py                   the single grade, glow, grain, dissolves
    typekit.py                end-card typography and the staged reveal
    audio.py                  score, sound design, de-click, EQ, mix, loudness
    timeline.py               the film: every beat against the locked narration
  final/
    altai_rehabilitation_v3.mp4 (+ .json manifest)
    altai_rehabilitation_commercial_v2.mp4   (preserved review master)
    altai_rehabilitation_commercial_v1.mp4   (preserved baseline)
  tests/
    V3_QC_REPORT.md           what was checked, and the numbers
    MOTION_TEST_REPORT.md     earlier capability check
    V2_QC_REPORT.md           earlier QC record
  render_altai_commercial.py  v2 renderer, retained and unmodified
  render_altai_commercial_v1.py, render_skier_motion_test.py, shots/…  retained
```

## Still open before release

* Owner approval of the cut, the mix and the staged stills.
* Factual, clinical and legal review of the copy (no claim in the film asserts a
  guaranteed return, a diagnosis or a service that has not been confirmed).
* Rights for the generated footage and the approved stills.
* A 9:16 social version, composed separately rather than blind-cropped (not
  built in this pass).
* Source quality: the clips are 1280 × 704 / 1344 × 768 and are upscaled; the
  AI artefacts in the fall (skis, gloves) are reduced by slow motion but not
  removed; the skier in the clips and the athlete in the interiors are different
  people and cannot be reconciled without new generation.
