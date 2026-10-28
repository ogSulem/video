# Altai rehabilitation commercial — v2 director's cut

## Deliverables

- **Current review master:** [`final/altai_rehabilitation_commercial_v2.mp4`](final/altai_rehabilitation_commercial_v2.mp4) — 77.00 s, 1920 × 1080, 24 fps, H.264 High/yuv420p, AAC-LC stereo 48 kHz. SHA-256: `86fdee75baf13a2183d219e34f65b9bd8ffe9c916a11722808ae0d3a79390410`.
- **Preserved baseline:** [`final/altai_rehabilitation_commercial_v1.mp4`](final/altai_rehabilitation_commercial_v1.mp4). V1 is not overwritten.
- **Test-first capability check:** [`tests/skier_motion_test_v1.mp4`](tests/skier_motion_test_v1.mp4), with [`tests/MOTION_TEST_REPORT.md`](tests/MOTION_TEST_REPORT.md). It is a six-second category-C animated still test—not generated video footage.
- **QC record:** [`tests/V2_QC_REPORT.md`](tests/V2_QC_REPORT.md).

## Reproduce v2

From the repository root, using Python 3.11 or newer:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r video/requirements.txt
.venv/bin/python video/render_altai_commercial.py --verify-only
.venv/bin/python video/render_altai_commercial.py
```

The default output is `video/final/altai_rehabilitation_commercial_v2.mp4`. The renderer refuses to overwrite an existing output unless `--force` is supplied. It uses the FFmpeg binary supplied by the pinned `imageio-ffmpeg` wheel and requires `libx264`; Pillow and NumPy are pinned in `requirements.txt`. A Cyrillic-capable DejaVu Serif/Sans font is required for the post-rendered end-card typography.

The previous v1 assembly script is retained as [`render_altai_commercial_v1.py`](render_altai_commercial_v1.py). The capability-test renderer is [`render_skier_motion_test.py`](render_skier_motion_test.py).

## Edit, assets, and motion provenance

- V2 uses the unchanged, hash-checked approved stills and approved Russian VO. It also uses three separate **provisional AI-generated stills** in `assets/`: a loss-of-control keyframe, supported-arrival keyframe, and wide Altai end-card landscape. These are new editorial inserts, not approval-locked references, and remain subject to owner review.
- The loss-of-control still precedes a separate approved aftermath still. The impact is implied by a short snow-white transition and a restrained designed sound accent; the aftermath is not presented as the fall itself.
- All apparent movement—including camera push/pan, drifting snow, brief breath/impact overlays, and the mountain-to-sky ending—is programmatic 2D compositing over stills. The skier's body does not articulate. There is **no genuine AI-generated motion footage, image-to-video, or live-action video** in v2.
- No video-generation tool, local GPU/model runtime, external video service, official logo/emblem file, or brand-font package was available in the audited session. The decorative motif in the locked Scene 10 reference is not an official logo and is not used as one. Exact approved brand copy is rendered in post: `РЕАБИЛИТАЦИОННЫЙ ЦЕНТР АЛТАЙ`, `Твой сезон продолжается.`, `altaysportreab.ru`.
- The original deterministic synthetic score/ambience includes alpine-air texture, sparse warm pad/pulse, a brief designed snow impact, and a near-silent bed after the fall. No third-party music, recorded SFX, or external audio service was used.
- Keep the v2 as a review master until the owner approves the provisional stills and the appropriate factual/clinical/legal, rights, and delivery-loudness checks are complete.
