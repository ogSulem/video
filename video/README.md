# Altai rehabilitation commercial render

The reproducible assembly script is [`render_altai_commercial.py`](render_altai_commercial.py). Its default deliverable is:

`video/final/altai_rehabilitation_commercial_v1.mp4`

## Render

From the repository root, using Python 3.11 or newer:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r video/requirements.txt
.venv/bin/python video/render_altai_commercial.py --verify-only
.venv/bin/python video/render_altai_commercial.py
```

The script uses the FFmpeg binary supplied by the pinned `imageio-ffmpeg` wheel and requires its `libx264` encoder. It uses a system Cyrillic-capable DejaVu Sans font (or another font path listed in the script). Existing outputs are not overwritten unless `--force` is explicitly supplied. The script verifies SHA-256 hashes of every approved still and the locked voice-over before and after rendering; it never edits those sources.

## Edit and media notes

- 77 seconds, 1920 × 1080, 24 fps, 16:9; H.264 video and AAC stereo audio at 48 kHz.
- Scenes follow the 20-beat timing in `editing/video_assembly_plan.md`. All apparent camera movement is restrained 2D pan/zoom over unchanged approved stills. There is no reference-image-to-video footage or genuine moving-camera footage in this render.
- The end card uses the approved Scene 10 backup background. The only added lettering is typeset in post with the exact owner-approved brand name, tagline, and URL; the existing mountain/trail mark remains decorative, not an official logo.
- The voice-over is the approved, unchanged `audio/voiceover/voiceover_ru_full_v1.mp3`.
- The bed is an original deterministic synthetic ambient score with a soft pulse, alpine-air texture, and one quiet designed transition accent. No third-party music, recorded SFX, or external media service was used. The synthetic bed is not a substitute for a future licensed/original-recorded final mix if one is required by the client.
- Treat this v1 as a review render, not an automatically approved public advertisement. Verify facility facts, brand/domain, claims, rights, and delivery requirements before release.
