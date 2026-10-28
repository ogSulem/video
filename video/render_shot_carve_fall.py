#!/usr/bin/env python3
"""Render the continuous 5-second "controlled carve -> soft-snow fall" shot.

The shot is authored as a chain of photoreal keyframes generated from the
approved character reference (REF-CHAR-01) and then animated as a single
continuous take:

  1. dense optical flow between neighbouring keyframes (DIS + iterative
     refinement), with forward/backward consistency weighting;
  2. a C1-continuous timeline places each output frame between two keyframes,
     so speed never snaps at a keyframe;
  3. a 180-degree shutter is simulated by integrating 7 sub-frame samples
     along the motion path (widening where the action is fastest), which turns
     residual wobble into real motion blur the way a real camera would;
  4. one continuous camera move (modest push-in plus a gentle follow) is
     applied to the whole shot, so framing never jumps;
  5. procedural snow -- ambient drift plus a volumetric powder burst staged at
     the moment of the fall -- is composited in screen space;
  6. a film finishing pass (lens softness, grain, vignette, gentle curve).

Usage:
    python3 video/render_shot_carve_fall.py [--force] [--preview]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from shotkit import flow as flowmod  # noqa: E402
from shotkit.camera import CameraMove  # noqa: E402
from shotkit.finish import finish_frame  # noqa: E402
from shotkit.snow import SnowSystem  # noqa: E402
from shotkit.timeline import Timeline  # noqa: E402

SHOT_DIR = ROOT / "shots" / "altai_carve_fall_v1"
KEY_DIR = SHOT_DIR / "keyframes"
OUT_DIR = SHOT_DIR / "out"

FPS = 24
DURATION = 5.0
WIDTH, HEIGHT = 1920, 1080

# (keyframe, time of that pose in seconds)
NODES = [
    ("kf01", 0.00),   # settled carve, edges holding
    ("kf01b", 0.55),  # knee deepens, downhill edge starts to give
    ("kf02", 1.35),   # grip lost: knees collapse, arms open
    ("kf02b", 2.10),  # weight going back, shoulders reacting
    ("kf03", 2.85),   # washout, pitching back over the tails
    ("kf04", 3.75),   # impact with the powder, snow burst
    ("kf05", 4.95),   # settled on the snow, dust hanging
]

# camera focus in normalised plate coordinates, one entry per node
FOCUS = [
    (0.545, 0.500),
    (0.548, 0.498),
    (0.575, 0.492),
    (0.578, 0.492),
    (0.535, 0.485),
    (0.570, 0.500),
    (0.548, 0.545),
]

# minor powder events: (time, (x, y) normalised, power, count)
SNOW_BURSTS = [
    (1.33, (0.55, 0.72), 0.30, 160),   # edge gives way
    (2.08, (0.53, 0.71), 0.45, 240),   # skis skid flat
    (2.84, (0.52, 0.70), 0.75, 420),   # washout
    (3.70, (0.52, 0.790), 1.30, 1100),  # impact burst, at the ski/snow contact
    (3.96, (0.50, 0.775), 1.05, 650),  # rebound spray
]

TRUST_SIGMA = 4.5   # lower = fall back to the nearer keyframe sooner (fewer ghosts)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_plate(path: Path) -> np.ndarray:
    """Keyframes are 16:9 but slightly wider than 1365 px; centre-crop."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    target_w = int(round(h * WIDTH / HEIGHT))
    if w > target_w:
        x0 = (w - target_w) // 2
        im = im.crop((x0, 0, x0 + target_w, h))
    return np.asarray(im)


def refine_flow(src, dst, base, iters=3):
    """Iterative DIS refinement: warp dst back on the current flow, re-solve."""
    g0 = cv2.cvtColor(src, cv2.COLOR_RGB2GRAY)
    g1 = cv2.cvtColor(dst, cv2.COLOR_RGB2GRAY)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    dis.setFinestScale(0)
    dis.setUseSpatialPropagation(True)
    flow = base.copy()
    for _ in range(iters):
        warped = flowmod.warp(dst, flow, 1.0)
        g1w = cv2.cvtColor(np.clip(warped, 0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        flow = dis.calc(g0, g1w, flow).astype(np.float32)
    return flow


def prepare_pairs(plates):
    """Forward/backward flow for each consecutive keyframe pair."""
    pairs = []
    for i in range(len(plates) - 1):
        a, b = plates[i], plates[i + 1]
        fab = flowmod.dense_flow(a, b)
        fba = flowmod.dense_flow(b, a)
        fab = refine_flow(a, b, fab)
        fba = refine_flow(b, a, fba)
        pairs.append((fab, fba))
    return pairs


def render_plate(rgb: np.ndarray, sub_times, timeline, plates, pairs):
    """Average several sub-frame samples: this is the shutter, not a crossfade."""
    acc = None
    for t in sub_times:
        u = float(timeline(t))
        u = min(max(u, 0.0), len(plates) - 1.0)
        i = int(np.floor(u))
        if i >= len(plates) - 1:
            i = len(plates) - 2
            a = 1.0
        else:
            a = u - i
        fab, fba = pairs[i]
        if a <= 0.004:
            frame = plates[i]
        elif a >= 0.996:
            frame = plates[i + 1]
        else:
            frame = flowmod.blend_keyframes(plates[i], plates[i + 1], fab, fba, a,
                                            trust_sigma=TRUST_SIGMA)
        acc = frame.astype(np.float32) if acc is None else acc + frame.astype(np.float32)
    return acc / len(sub_times)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite an existing render")
    ap.add_argument("--preview", action="store_true", help="render every 4th frame only")
    ap.add_argument("--crf", type=int, default=16)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "altai_carve_fall_v1.mp4"
    if out_path.exists() and not args.force:
        print(f"refusing to overwrite {out_path} (pass --force)")
        return 2

    key_paths = [KEY_DIR / f"{name}.png" for name, _ in NODES]
    missing = [str(p) for p in key_paths if not p.exists()]
    if missing:
        print("missing keyframes:\n  " + "\n  ".join(missing))
        return 2

    t0 = time.time()
    plates = [load_plate(p) for p in key_paths]
    h, w = plates[0].shape[:2]
    print(f"plates {w}x{h}  x{len(plates)}  ({time.time() - t0:.1f}s)")

    pairs = prepare_pairs(plates)
    print(f"flow fields ready ({time.time() - t0:.1f}s)")

    timeline = Timeline([t for _, t in NODES])
    cam = CameraMove(
        timeline, FOCUS,
        zoom_start=1.00, zoom_end=1.10,
        drift=(0.006, 0.004),
        duration=DURATION,
    )
    snow = SnowSystem(WIDTH, HEIGHT, FPS, DURATION, seed=11,
                      drift_flakes=70, bursts=[
                          {"t0": t, "center": c, "power": p, "count": n}
                          for t, c, p, n in SNOW_BURSTS
                      ])

    n_frames = int(round(FPS * DURATION))
    base_shutter = 0.5 / FPS * 0.85     # 180-degree-ish shutter, slightly held
    sub = 7

    ffmpeg = None
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # pragma: no cover
        from shutil import which
        ffmpeg = which("ffmpeg")
    if not ffmpeg:
        print("ffmpeg not found")
        return 2

    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS), "-i", "-",
        "-an",
        "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf),
        "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-metadata", "title=Altai rehab commercial - carve and fall, 5s single take",
        str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    step = 4 if args.preview else 1
    for idx in range(0, n_frames, step):
        t = idx / FPS
        # faster motion gets a slightly longer shutter, as on a real camera
        speed = abs(float(timeline(min(t + 0.5 / FPS, DURATION)) - timeline(max(t - 0.5 / FPS, 0.0))))
        shutter = base_shutter * float(np.clip(0.55 + 0.75 * speed, 0.55, 1.5))
        sub_times = [t + (k / (sub - 1) - 0.5) * shutter for k in range(sub)]
        sub_times = [min(max(x, 0.0), DURATION) for x in sub_times]
        base = render_plate(plates, sub_times, timeline, plates, pairs)

        # continuous camera move
        moves = [cam.render(np.clip(base, 0, 255).astype(np.uint8), x) for x in (sub_times[0], t, sub_times[-1])]
        # blend the camera positions across the shutter so the push-in is smooth
        base_cam = (moves[0].astype(np.float32) * 0.25
                    + moves[1].astype(np.float32) * 0.5
                    + moves[2].astype(np.float32) * 0.25)

        # upscale the plate to delivery size
        full = cv2.resize(np.clip(base_cam, 0, 255).astype(np.uint8), (WIDTH, HEIGHT),
                          interpolation=cv2.INTER_LANCZOS4).astype(np.float32)

        full = _apply_snow(full, snow, t, seed=idx)
        full = finish_frame(full, t, seed=idx, grain=1.3)
        proc.stdin.write(np.clip(full, 0, 255).astype(np.uint8).tobytes())
        if idx % 24 == 0:
            print(f"  frame {idx + 1}/{n_frames}  ({time.time() - t0:.1f}s)")

    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        print(f"ffmpeg failed with code {rc}")
        return rc

    print(f"wrote {out_path}  ({time.time() - t0:.1f}s)")

    manifest = {
        "output": str(out_path.relative_to(ROOT)),
        "sha256": sha256(out_path),
        "duration_s": DURATION,
        "fps": FPS,
        "frames": n_frames,
        "size": [WIDTH, HEIGHT],
        "keyframes": [
            {"file": f"shots/altai_carve_fall_v1/keyframes/{n}.png",
             "t": t, "sha256": sha256(KEY_DIR / f"{n}.png")}
            for n, t in NODES
        ],
    }
    (OUT_DIR / "altai_carve_fall_v1.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return 0


_CLOUD_TILES: dict = {}


def _cloud_texture(h, w):
    """A stable billow field. One instance per size, drifting over time.

    Re-seeding this per frame would make the spray shimmer; powder has to have
    a persistent, coherent structure that only drifts and dissipates.
    """
    key = (h, w)
    if key in _CLOUD_TILES:
        return _CLOUD_TILES[key]
    rng = np.random.default_rng(4242)
    # two octaves, tiling, so the field can scroll without a seam
    acc = np.zeros((h, w), dtype=np.float32)
    for octave, sigma in ((64, 9.0), (32, 4.0)):
        base = rng.normal(0.0, 1.0, (octave, octave)).astype(np.float32)
        base = np.tile(base, (int(np.ceil(h / octave)), int(np.ceil(w / octave))))[:h, :w]
        acc += cv2.GaussianBlur(base, (0, 0), sigma) * (1.0 if octave == 64 else 0.6)
    acc = (acc - acc.min()) / max(acc.max() - acc.min(), 1e-6)
    tex = 0.55 + 0.7 * acc
    _CLOUD_TILES[key] = tex
    return tex


def _apply_snow(img, snow, t, seed=0):
    """Composite spray as soft, structured powder rather than glow."""
    near, cloud = snow.layer(t)
    out = img.astype(np.float32) / 255.0
    h, w = out.shape[:2]
    tex = _cloud_texture(h, w)
    # slow drift + per-frame lateral offset so visible structure evolves rather
    # than flickering: a few pixels per frame, in one direction
    dx = int(-16.0 * t) % w
    dy = int(-9.0 * t) % h
    tex = np.roll(np.roll(tex, dy, axis=0), dx, axis=1)
    for layer, gain in ((near, 0.18), (cloud, 0.34)):
        if layer.max() <= 0.001:
            continue
        m = np.clip(layer * gain, 0.0, 1.0) * tex
        m = np.clip(m, 0.0, 0.9)[..., None]
        tint = np.array([0.955, 0.975, 1.0], dtype=np.float32)  # cool white
        out = out * (1.0 - m) + m * tint
    return np.clip(out * 255.0, 0, 255)


if __name__ == "__main__":
    raise SystemExit(main())
