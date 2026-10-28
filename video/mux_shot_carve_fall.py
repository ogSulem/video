#!/usr/bin/env python3
"""Mux the silent picture master and the designed sound bed into the delivery file."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOT = ROOT / "shots" / "altai_carve_fall_v1"
PICTURE = SHOT / "out" / "altai_carve_fall_v1.mp4"
AUDIO = SHOT / "out" / "altai_carve_fall_v1_audio.wav"
OUT = SHOT / "final" / "altai_carve_fall_v1_5s.mp4"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    for p in (PICTURE, AUDIO):
        if not p.exists():
            print(f"missing input: {p}")
            return 2
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists() and not args.force:
        print(f"refusing to overwrite {OUT} (pass --force)")
        return 2

    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(PICTURE), "-i", str(AUDIO),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart",
        "-metadata", "title=Altai rehabilitation - carve and fall, 5s single take",
        str(OUT),
    ]
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        print("mux failed")
        return rc

    info = subprocess.run([ffmpeg, "-hide_banner", "-i", str(OUT)],
                          capture_output=True, text=True).stderr
    manifest = {
        "delivery": str(OUT.relative_to(ROOT.parent)),
        "sha256": sha256(OUT),
        "picture_master": str(PICTURE.relative_to(ROOT.parent)),
        "picture_sha256": sha256(PICTURE),
        "audio_master": str(AUDIO.relative_to(ROOT.parent)),
        "audio_sha256": sha256(AUDIO),
    }
    (SHOT / "final" / "altai_carve_fall_v1_5s.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {OUT}")
    print(info.strip().splitlines()[-4:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
