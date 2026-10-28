#!/usr/bin/env python3
"""Insert 4 AI hero clips into the approved 77-second assembly.

The approved v2 cut is the backbone: its picture is used frame for frame, its
already-approved audio mix (including the locked Russian voice-over) is carried
over untouched. Four windows of that timeline are optionally replaced by
generated clips, with short cross-dissolves at the edges so the joins read as a
cut in the edit rather than as a glitch.

Clips are normalised to 1920x1080 / 24 fps by centre-cropping (never stretching),
so a 16:9 generator output of any size fits.

Usage:
    python3 video/tools/assemble_hero_clips.py --force
    python3 video/tools/assemble_hero_clips.py --force --clipA my_a.mp4 --clipA-at 1.0 --clipA-len 11

Windows default to the plan in production/video_generation_pack/01_plan_i_tayming.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "video" / "final" / "altai_rehabilitation_commercial_v2.mp4"
CLIP_DIR = ROOT / "video" / "shots" / "ai_hero_clips"
OUT_DIR = ROOT / "video" / "final"
OUT = OUT_DIR / "altai_rehabilitation_hero_v1.mp4"

W, H, FPS = 1920, 1080, 24
FADE = 0.40  # seconds of cross-dissolve at each window edge


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fit_frame(frame: np.ndarray) -> np.ndarray:
    """Centre-crop to 16:9 then resize to delivery size. No stretching."""
    h, w = frame.shape[:2]
    target = W / H
    if w / h > target:
        new_w = int(round(h * target))
        x0 = (w - new_w) // 2
        frame = frame[:, x0:x0 + new_w]
    else:
        new_h = int(round(w / target))
        y0 = (h - new_h) // 2
        frame = frame[y0:y0 + new_h, :]
    if frame.shape[1] != W or frame.shape[0] != H:
        frame = cv2.resize(frame, (W, H), interpolation=cv2.INTER_LANCZOS4)
    return frame


def eased(x: float) -> float:
    x = float(np.clip(x, 0.0, 1.0))
    return x * x * (3.0 - 2.0 * x)


class ClipReader:
    """Sequential reader for one window; seeks once, then reads forward."""

    def __init__(self, path: Path):
        self.path = path
        self.cap = cv2.VideoCapture(str(path))
        if not self.cap.isOpened():
            raise RuntimeError(f"cannot open clip {path}")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or FPS
        self.frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.pos = 0
        self.last = None

    @property
    def duration(self) -> float:
        return self.frames / self.fps if self.fps else 0.0

    def frame_at(self, seconds: float):
        want = int(round(seconds * self.fps))
        want = max(0, min(want, self.frames - 1))
        if want < self.pos:  # rewind is rare; just seek
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, want)
            self.pos = want
        while self.pos < want:
            ok, _ = self.cap.read()
            if not ok:
                return self.last
            self.pos += 1
        ok, frame = self.cap.read()
        if not ok:
            return self.last
        self.pos += 1
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.last = fit_frame(frame)
        return self.last

    def release(self):
        self.cap.release()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(BASE))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--no-audio", action="store_true", help="write picture-only (for QC)")
    for tag, default_at, default_len in (("A", 1.0, 11.0), ("B", 17.0, 7.0),
                                         ("C", 28.0, 8.0), ("D", 62.0, 10.0)):
        ap.add_argument(f"--clip{tag}", default=str(CLIP_DIR / f"clip{tag}.mp4"))
        ap.add_argument(f"--clip{tag}-at", type=float, default=default_at)
        ap.add_argument(f"--clip{tag}-len", type=float, default=default_len)
    args = ap.parse_args()

    base_path = Path(args.base)
    out_path = Path(args.out)
    if not base_path.exists():
        print(f"missing base: {base_path}")
        return 2
    if out_path.exists() and not args.force:
        print(f"refusing to overwrite {out_path} (pass --force)")
        return 2
    out_path.parent.mkdir(parents=True, exist_ok=True)

    base = cv2.VideoCapture(str(base_path))
    if not base.isOpened():
        print(f"cannot open base {base_path}")
        return 2
    fps = base.get(cv2.CAP_PROP_FPS) or FPS
    total = int(base.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"base: {total} frames @ {fps:.3f} fps = {total / fps:.2f}s")

    windows = []
    for tag, at_attr, len_attr in (("A", "clipA_at", "clipA_len"),
                                   ("B", "clipB_at", "clipB_len"),
                                   ("C", "clipC_at", "clipC_len"),
                                   ("D", "clipD_at", "clipD_len")):
        path = Path(getattr(args, f"clip{tag}"))
        start = float(getattr(args, at_attr))
        length = float(getattr(args, len_attr))
        if not path.exists():
            print(f"clip {tag}: not found ({path}) -> window left as approved base picture")
            continue
        try:
            reader = ClipReader(path)
        except RuntimeError as exc:
            print(f"clip {tag}: {exc} -> skipped")
            continue
        usable = min(length, reader.duration)
        if usable < length:
            print(f"clip {tag}: only {reader.duration:.2f}s long, window shortened "
                  f"{length:.2f}s -> {usable:.2f}s")
        if usable < 0.5:
            print(f"clip {tag}: too short, skipped")
            reader.release()
            continue
        windows.append({"tag": tag, "start": start, "len": usable, "reader": reader,
                        "file": path.name})
        print(f"clip {tag}: {path.name}  in at {start:.2f}s for {usable:.2f}s "
              f"({reader.fps:.2f} fps source)")

    if not windows:
        print("no clips found: nothing to assemble (the approved cut already stands)")
        return 2

    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    silent = out_path.with_suffix(".picture.mp4")
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
        "-i", "-", "-an",
        "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        str(silent),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    n_out = 0
    for idx in range(total):
        t = idx / fps
        ok, frame = base.read()
        if not ok:
            break
        out = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32)

        for w in windows:
            t0, t1 = w["start"], w["start"] + w["len"]
            if not (t0 - FADE <= t <= t1 + FADE):
                continue
            local = t - t0 + FADE
            clip_frame = w["reader"].frame_at(max(0.0, local))
            if clip_frame is None:
                break
            # dissolve in over FADE at the start, out over FADE at the end
            a = 1.0
            if t < t0 + FADE:
                a = eased((t - (t0 - FADE)) / (2 * FADE))
            elif t > t1 - FADE:
                a = eased(1.0 - (t - (t1 - FADE)) / (2 * FADE))
            a = float(np.clip(a, 0.0, 1.0))
            out = out * (1 - a) + clip_frame.astype(np.float32) * a
            break

        proc.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
        n_out += 1
        if n_out % 240 == 0:
            print(f"  {n_out}/{total} frames")

    proc.stdin.close()
    if proc.wait() != 0:
        print("encoder failed")
        return 3
    base.release()
    for w in windows:
        w["reader"].release()

    final = silent
    if not args.no_audio:
        cmd2 = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(silent), "-i", str(base_path),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "copy", "-shortest",
            "-movflags", "+faststart",
            "-metadata", "title=Altai rehabilitation - hero cut with generated motion",
            str(out_path),
        ]
        if subprocess.run(cmd2).returncode != 0:
            print("muxing the approved audio failed")
            return 4
        silent.unlink(missing_ok=True)
        final = out_path

    def rel(p: Path) -> str:
        try:
            return str(p.resolve().relative_to(ROOT))
        except ValueError:
            return str(p)

    manifest = {
        "delivery": rel(final),
        "sha256": sha256(final),
        "base": rel(base_path),
        "base_sha256": sha256(base_path),
        "windows": [{"clip": w["tag"], "file": w["file"],
                     "at_s": w["start"], "len_s": w["len"]} for w in windows],
        "frames": n_out, "fps": fps, "size": [W, H],
    }
    (final.parent / (final.stem + ".json")).write_text(
        json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {final}  ({n_out / fps:.2f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
