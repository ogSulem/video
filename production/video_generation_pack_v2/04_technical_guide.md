# Technical guide — download the MP4s and place them for assembly

Nothing here renders or re-encodes the commercial. It only gets the four generated
files into the folder the assembler reads.

---

## 1. Where the files go

```
video/shots/ai_hero_clips/
├── clipA.mp4     ← fall
├── clipB.mp4     ← rescue
├── clipC.mp4     ← rehabilitation
└── clipD.mp4     ← return
```

Exact names, lowercase, `.mp4`. The assembler looks for `clip<X>.mp4` and skips any
clip that is missing — three, two or one clip is a valid assembly.

The folder is git-ignored for `*.mp4`, so clips do not bloat the repository history.
If you want them committed for review, either force-add them
(`git add -f video/shots/ai_hero_clips/clipA.mp4`) or hand them to me through the
session and I will keep them local.

## 2. Downloading

- Generated files are usually served as a temporary URL. Download within the
  advertised window (often 24–72 hours) — do not rely on the link afterwards.
- Save directly under the target name; avoid re-exporting through a phone editor or
  a messaging app, which re-encodes and drops the frame rate.
- If the service offers resolutions, take the **highest 16:9** available (1080p or
  above). The assembler centre-crops to 1920×1080 and never stretches, so a 16:9
  source at any size is safe; a non-16:9 source loses edges.
- Keep the original download untouched until the clip is accepted.

## 3. Sanity check before assembly

```bash
.venv/bin/python video/tools/check_hero_clips.py
```

Prints, per clip: found/absent, container, codec, resolution, fps, duration, frame
count and a SHA-256. It also flags the two things that actually break the assembly:
a non-16:9 aspect ratio, and a clip shorter than 1 s.

Equivalent one-liner if you prefer ffmpeg directly:

```bash
.venv/bin/python -c "import imageio_ffmpeg,subprocess,sys; \
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-i','video/shots/ai_hero_clips/clipA.mp4'])"
```

## 4. Optional fine-tune of the slot

The assembler takes per-clip overrides; defaults are set to the edit plan in
`05_vo_mapping.md`:

```bash
.venv/bin/python video/tools/assemble_hero_clips.py --force \
  --clipA-at 0.0  --clipA-len 11 \
  --clipB-at 11.0 --clipB-len 8 \
  --clipC-at 24.0 --clipC-len 10 \
  --clipD-at 62.0 --clipD-len 10
```

- `--clipX-at` = start time in the 77-second timeline.
- `--clipX-len` = window length; if the clip is shorter, the window shrinks to fit
  and the approved stills carry the remainder.
- If a clip is **longer** than its window, the extra tail is simply not used. To use a
  later part of a clip instead of its opening, trim it first with ffmpeg and save as a
  temporary file — do not overwrite the original download.

## 5. Assembly (a separate, deliberate step)

Only after the clips are in place and accepted:

```bash
.venv/bin/python video/tools/assemble_hero_clips.py --force
```

Result: `video/final/altai_rehabilitation_hero_v1.mp4` — 77.00 s, 1920×1080, 24 fps,
approved Russian voice-over carried over by stream copy (not re-encoded).
`V1` and `V2` are read-only inputs in that process and are never overwritten.

`--no-audio` writes a picture-only file for a quick look without the mix.

## 6. If a clip is rejected

Delete the file, keep the note about why (morphing, extra limbs, axis flip, text
artefacts), and regenerate with the same prompt plus the specific negative terms.
Do not try to "fix" morphing with speed ramps or cross-dissolves — in a 77-second film
those read as glitches.

## 7. Aspect, frame rate, naming pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| Clip appears stretched | non-16:9 source width | regenerate 16:9, or accept centre-crop |
| Motion stutters against stills | source is 30/60 fps and pitched oddly | assembler outputs 24 fps; source above 24 fps is fine |
| Clip ignored by assembler | wrong name/case or `.mov` | rename to exactly `clipB.mp4` |
| Audio from clip leaks in | clip had its own soundtrack | assembler takes the approved mix only; clip audio is discarded |
