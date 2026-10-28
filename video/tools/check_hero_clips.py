#!/usr/bin/env python3
"""Inspect the generated hero clips before assembly. Read-only.

Prints container, codec, resolution, fps, duration and SHA-256 for each of
video/shots/ai_hero_clips/clip{A,B,C,D}.mp4, and flags the things that actually
break the assembly: a missing file, a non-16:9 source, a clip shorter than one
second. Writes nothing; never touches the approved assets.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLIP_DIR = ROOT / "video" / "shots" / "ai_hero_clips"
SLOTS = {"A": (0.0, 11.0), "B": (11.0, 8.0), "C": (24.0, 10.0), "D": (62.0, 10.0)}


def ffprobe_json(ffmpeg: str, path: Path):
    """Use the bundled ffmpeg's sibling ffprobe when present, else parse -i output."""
    probe = Path(ffmpeg).with_name("ffprobe")
    if probe.exists():
        out = subprocess.run([str(probe), "-v", "error", "-show_streams", "-show_format",
                              "-of", "json", str(path)],
                             capture_output=True, text=True)
        if out.returncode == 0:
            return json.loads(out.stdout or "{}")
    return {}


def parse_ffmpeg_stderr(text: str) -> dict:
    info = {}
    for line in text.splitlines():
        s = line.strip()
        if "Duration:" in s:
            info["duration_str"] = s.split("Duration:")[1].split(",")[0].strip()
        if "Video:" in s and "Stream" in s:
            for tok in s.replace(",", " ").split():
                if "x" in tok and tok.replace("x", "").isdigit():
                    w, h = tok.split("x")
                    if w.isdigit() and h.isdigit() and int(w) > 100:
                        info["width"], info["height"] = int(w), int(h)
                if tok.endswith("fps"):
                    try:
                        info["fps"] = float(tok[:-3])
                    except ValueError:
                        pass
    return info


def main() -> int:
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg = "ffmpeg"

    if not CLIP_DIR.exists():
        print(f"folder does not exist yet: {CLIP_DIR}")
        print("create it and drop clipA.mp4 … clipD.mp4 in it")
        return 1

    found = 0
    problems = []
    for tag, (at_s, want_len) in SLOTS.items():
        path = CLIP_DIR / f"clip{tag}.mp4"
        print(f"\n=== clip{tag}  (slot {at_s:.1f}s, wanted {want_len:.0f}s)")
        if not path.exists():
            print("  not found — window stays on approved stills")
            continue
        found += 1
        size_mb = path.stat().st_size / 1e6
        sha = hashlib.sha256(path.read_bytes()).hexdigest()

        meta = ffprobe_json(ffmpeg, path)
        if meta.get("streams"):
            v = next((s for s in meta["streams"] if s.get("codec_type") == "video"), {})
            w, h = int(v.get("width", 0)), int(v.get("height", 0))
            fr = v.get("avg_frame_rate", "0/1")
            try:
                num, den = fr.split("/")
                fps = float(num) / float(den) if float(den) else 0.0
            except Exception:
                fps = 0.0
            dur = float(meta.get("format", {}).get("duration", 0.0) or 0.0)
            codec = v.get("codec_name", "?")
            print(f"  {w}x{h}  {codec}  {fps:.3f} fps  {dur:.2f}s  {size_mb:.1f} MB")
        else:
            stderr = subprocess.run([str(ffmpeg), "-hide_banner", "-i", str(path)],
                                    capture_output=True, text=True).stderr
            info = parse_ffmpeg_stderr(stderr)
            w, h = info.get("width", 0), info.get("height", 0)
            fps, codec = info.get("fps", 0.0), "?"
            dur = 0.0
            ds = info.get("duration_str", "")
            if ":" in ds:
                try:
                    hh, mm, ss = ds.split(":")
                    dur = int(hh) * 3600 + int(mm) * 60 + float(ss)
                except ValueError:
                    pass
            print(f"  {w}x{h}  {codec}  {fps:.3f} fps  {dur:.2f}s  {size_mb:.1f} MB")

        print(f"  sha256 {sha}")

        if w and h and abs((w / h) - (16 / 9)) > 0.02:
            msg = f"clip{tag}: aspect {w}x{h} is not 16:9 — centre-crop will lose the sides"
            print("  WARNING " + msg)
            problems.append(msg)
        if dur and dur < 1.0:
            msg = f"clip{tag}: only {dur:.2f}s — too short to use"
            print("  WARNING " + msg)
            problems.append(msg)
        if dur and dur < want_len:
            print(f"  note: shorter than the {want_len:.0f}s window; the window will shrink "
                  f"to {dur:.2f}s and stills will carry the rest")
        if dur and dur > want_len:
            print(f"  note: longer than the window; only the first {want_len:.0f}s will be used")
        if fps and abs(fps - 24.0) > 0.01:
            print(f"  note: source is {fps:.2f} fps; the assembly runs at 24 fps")

    print(f"\n{found}/4 clip(s) present in {CLIP_DIR}")
    if problems:
        print("resolve before assembling:")
        for p in problems:
            print("  - " + p)
        return 1
    if found:
        print("next (deliberate step): .venv/bin/python video/tools/assemble_hero_clips.py --force")
    return 0


if __name__ == "__main__":
    sys.exit(main())
