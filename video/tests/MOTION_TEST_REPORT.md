# Motion capability test — skier still

**Test-first gate:** completed before the director's rework. The six-second test is a technical capability check, not a commercial or a claim of generated video.

## Render

- **File:** `video/tests/skier_motion_test_v1.mp4`
- **Duration / frame rate / frame count:** 6.00 seconds / 24 fps / 144 frames
- **Picture:** 1920 × 1080, 16:9, H.264 High Profile, yuv420p
- **Audio:** AAC-LC, stereo
- **File size:** 2,397,447 bytes
- **SHA-256:** `972cf6ecb94bf898f46c608a99bb1c02db427d0eb9de92f38bf8056f1cb4e167`
- **Locked test source:** `references/characters/REF-CHAR-01-master-skier.png`, SHA-256 `3b0bbeb5199e254930a9938f9dd1b2371c9fbbcb33311d1d6af494b9de4cc407`. The test renderer refuses a source-hash mismatch.

## What the test demonstrates

The renderer adds a restrained programmed pan/zoom and deterministic drifting snow over the unchanged character-reference still. Frames sampled at 0.5, 3.0, and 5.5 seconds show changing framing and snow positions; the skier's pose and body do not articulate.

**Classification: category C — animated still / procedural compositing.** It is not AI-generated moving footage, image-to-video, a real camera move, or subject animation. Do not describe the test as generated video.

## Capability and provenance notes

- The active session exposes image generation for still images; no video-generation tool or image-to-video workflow was available in the inspected session tools. No local GPU/model runtime was found in the audited environment, and no external video service/API was established.
- The earlier described green-field/cloud effect could not be reproduced from the current repository: no corresponding clip, asset, script, or prompt/workflow is accessible here. Its prior provenance remains unknown; no inference is made about how it was produced.
- The renderer uses PyPI-provided `imageio-ffmpeg`, Pillow, and NumPy. The system package route was already checked and Debian mirrors were unreachable; no further attempt was needed.
- This limitation did not block producing a better still-based v2 assembly. The new loss-of-control, supported-arrival, and end-card landscape images are **still images** only; motion in v2 remains programmatic 2D framing and compositing.

## Reproduction

From the repository root, after installing `video/requirements.txt`:

```bash
.venv/bin/python video/render_skier_motion_test.py
```
