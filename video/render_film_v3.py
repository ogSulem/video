#!/usr/bin/env python3
"""Render RETURN TO THE SLOPE v3 — picture, score, mix, master.

    python3 video/render_film_v3.py --verify-only     # check pins + plan
    python3 video/render_film_v3.py --preview 8 20    # 12 s silent proof
    python3 video/render_film_v3.py                   # full 78 s master

The renderer is a single deterministic pass: it pulls every frame through the
filmkit pipeline and pipes raw RGB into FFmpeg's x264 encoder while the score
is synthesised separately, then muxes the master with FFmpeg's AAC encoder.

Nothing is downloaded, nothing is overwritten without --force, and every source
is hash-verified before the first frame.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "video"))

from filmkit import audio as film_audio          # noqa: E402
from filmkit import sources, timeline           # noqa: E402
from filmkit.timeline import FPS, HEIGHT, WIDTH, film_duration   # noqa: E402

OUT_DIR = ROOT / "video" / "final"
DEFAULT_OUT = OUT_DIR / "altai_rehabilitation_v3.mp4"
TMP = ROOT / ".qc" / "v3"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------
def print_plan(shots: list[timeline.Shot]) -> None:
    print(f"\n{'#':>2}  {'in':>6} {'out':>6} {'len':>5}  {'kind':6s} {'source':12s} name")
    print("-" * 78)
    for i, shot in enumerate(shots, 1):
        origin = shot.source or "-"
        if shot.kind == "clip":
            first = shot._retimer.positions[0] if shot._retimer else shot.in_frame
            last = shot._retimer.positions[-1] if shot._retimer else shot.in_frame
            origin = f"{shot.source}[{first:.0f}-{last:.0f}]"
        print(f"{i:2d}  {shot.start:6.2f} {shot.end:6.2f} {shot.duration:5.2f}  "
              f"{shot.kind:6s} {origin:12s} {shot.name}")
    total = shots[-1].end
    print("-" * 78)
    print(f"total {total:.2f} s  =  {int(round(total * FPS))} frames @ {FPS} fps, "
          f"{WIDTH}x{HEIGHT}")
    moving = sum(s.duration for s in shots if s.kind == "clip")
    print(f"generated motion footage: {moving:.2f} s "
          f"({moving / total * 100:.0f}% of the film); "
          f"staged stills: {sum(s.duration for s in shots if s.kind == 'still'):.2f} s")


# --------------------------------------------------------------------------
def encode_picture(shots: list[timeline.Shot], out_path: Path,
                   start: float = 0.0, end: float | None = None,
                   crf: int = 17, preset: str = "medium") -> int:
    from imageio_ffmpeg import get_ffmpeg_exe

    end = end if end is not None else film_duration(shots)
    first = int(round(start * FPS))
    last = int(round(end * FPS))
    count = max(1, last - first)

    cmd = [
        get_ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS), "-i", "pipe:0",
        "-an", "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
        "-g", "48", "-keyint_min", "24", "-sc_threshold", "0",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    started = time.time()
    try:
        for n in range(count):
            index = first + n
            t = index / FPS
            frame = timeline.render_frame(shots, t)
            proc.stdin.write(np.ascontiguousarray(frame).tobytes())
            if (n + 1) % 24 == 0 or n + 1 == count:
                done = n + 1
                elapsed = time.time() - started
                rate = done / max(elapsed, 1e-6)
                eta = (count - done) / max(rate, 1e-6)
                print(f"\r  frame {done}/{count}  {rate:5.2f} fps  "
                      f"elapsed {elapsed/60:4.1f}m  eta {eta/60:4.1f}m", end="", flush=True)
        proc.stdin.close()
    except BrokenPipeError:
        print("\nencoder closed the pipe early", file=sys.stderr)
    if proc.wait() != 0:
        raise RuntimeError("x264 encode failed")
    print()
    return count


# --------------------------------------------------------------------------
def build_master(shots: list[timeline.Shot], out_path: Path, crf: int,
                 preset: str, force: bool, declick: bool = True,
                 vo_eq: bool = True) -> dict:
    TMP.mkdir(parents=True, exist_ok=True)
    duration = timeline.film_duration(shots)
    picture = TMP / "picture.mp4"

    # ---- audio first: if anything is wrong with the mix, fail before the
    # ---- hour of picture rendering rather than after it
    print("\n[1/4] score")
    plan = timeline.music_plan(duration)
    score = film_audio.render_score(plan)
    print(f"  score rendered: {score.shape[0] / film_audio.SR:.2f} s")

    print("[2/4] voice-over + mix")
    vo = film_audio.decode_voiceover(sources.verify(quiet=True)["voiceover"])
    print(f"  voice-over decoded: {vo.shape[0] / film_audio.SR:.2f} s "
          f"(approved file, byte-identical)")
    vo, repaired = film_audio.declick(vo) if declick else (vo, [])
    if repaired:
        print(f"  codec-artefact repair on the placement copy: {len(repaired)} burst(s) "
              f"across {len(set(round(t, 1) for t, _ in repaired))} spot(s)")
    if vo_eq:
        peak_before = float(np.abs(vo).max())
        vo = film_audio.eq_curve(vo, film_audio.SR, film_audio.VO_EQ)
        peak_after = float(np.abs(vo).max())
        if peak_after > 0:
            vo *= peak_before / peak_after
        print(f"  broadcast voice curve on the placement copy (peak held at {peak_before:.2f})")
    if len(vo) / film_audio.SR + timeline.VO_OFFSET > duration:
        raise RuntimeError("narration no longer fits the picture plan")
    vo_placed = np.zeros((int(round(duration * film_audio.SR)), 2), np.float32)
    offset = int(timeline.VO_OFFSET * film_audio.SR)
    vo_placed[offset:offset + len(vo)] = vo
    score_padded = np.zeros_like(vo_placed)
    score_padded[: min(len(score), len(vo_placed))] = score[: len(vo_placed)]
    mixed, calib = film_audio.mix_film(vo_placed, score_padded)
    print(f"  bed balance: {calib}")
    mastered, loud = film_audio.normalize(mixed)
    mix_path = TMP / "mix.wav"
    film_audio.write_wav(mix_path, mastered)
    print(f"  loudness: {loud}")

    print("\n[3/4] picture")
    count = encode_picture(shots, picture, crf=crf, preset=preset)

    print("[4/4] master")
    from imageio_ffmpeg import get_ffmpeg_exe
    cmd = [
        get_ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(picture), "-i", str(mix_path),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart",
        "-metadata", "title=RETURN TO THE SLOPE — rehabilitation centre Altai",
        "-metadata", "comment=Picture: three generated clips re-timed with optical flow; "
                     "approved stills staged as depth-layered living stills; "
                     "original score; end card typeset in post.",
        str(out_path),
    ]
    if subprocess.run(cmd).returncode != 0:
        raise RuntimeError("master mux failed")
    print(f"  wrote {out_path.relative_to(ROOT)}")

    manifest = {
        "delivery": str(out_path.relative_to(ROOT)),
        "sha256": sha256(out_path),
        "duration_s": round(duration, 3),
        "frames": count,
        "fps": FPS,
        "size": [WIDTH, HEIGHT],
        "video": {"codec": "h264", "profile": "high", "pix_fmt": "yuv420p",
                  "crf": crf, "preset": preset, "colorspace": "bt709"},
        "audio": {"codec": "aac", "bitrate": "192k", "sample_rate": 48000,
                  "channels": 2, "loudness": loud, "balance": calib},
        "voiceover": {
            "file": "audio/voiceover/voiceover_ru_full_v1.mp3",
            "offset_s": timeline.VO_OFFSET,
            "file_modified": False,
            "codec_artefact_repairs_s": [round(t, 3) for t, _ in repaired],
            "mix_eq": "broadcast voice curve on the placement copy" if vo_eq else "none",
            "note": "the approved MP3 is byte-identical; the repair and the voice "
                    "curve are applied to the in-memory placement copy only",
        },
        "sources": {k: {"file": v[0], "sha256": v[1], "kind": v[2]}
                    for k, v in sources.PINNED.items()},
        "shots": [{"name": s.name, "in": round(s.start, 3), "out": round(s.end, 3),
                   "kind": s.kind, "source": s.source} for s in shots],
    }
    manifest_path = out_path.with_suffix(".json")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"  manifest: {manifest_path.relative_to(ROOT)}")
    return manifest


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--preview", nargs=2, type=float, metavar=("START", "END"),
                    help="render only this window, silent, for checking")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--crf", type=int, default=20,
                    help="x264 quality; 20 is visually transparent on this material "
                         "and lands near 5-6 Mbit/s for 1080p24")
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--no-declick", dest="declick", action="store_false",
                    help="keep the raw decode, including the MP3 click at ~22.9 s")
    ap.add_argument("--no-vo-eq", dest="vo_eq", action="store_false",
                    help="mix the narration with no corrective EQ at all")
    args = ap.parse_args()

    print("verifying approved sources")
    paths = sources.verify()

    print("\nbuilding shots")
    shots = timeline.build_shots(paths, verify_only=args.verify_only)
    print_plan(shots)
    if args.verify_only:
        return 0

    TMP.mkdir(parents=True, exist_ok=True)
    if args.preview:
        start, end = args.preview
        out = args.out or (TMP / f"preview_{start:.0f}_{end:.0f}.mp4")
        print(f"\npreview {start:.1f}-{end:.1f} s -> {out.relative_to(ROOT)}")
        encode_picture(shots, out, start=start, end=end, crf=args.crf,
                       preset=args.preset)
        print(f"  wrote {out}")
        return 0

    out = args.out or DEFAULT_OUT
    if out.exists() and not args.force:
        print(f"\nrefusing to overwrite {out} (pass --force)")
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_master(shots, out, args.crf, args.preset, args.force,
                             declick=args.declick, vo_eq=args.vo_eq)
    print("\ndone. delivery:", manifest["delivery"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
