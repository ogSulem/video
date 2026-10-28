#!/usr/bin/env python3
"""Render a 6-second capability test from the locked skier master still.

This is deliberately a category-C test: programmatic camera movement and
procedural snow/air overlays over one unchanged still. It is not AI-generated
video and does not animate the skier's joints. The script is useful to evaluate
the maximum visual motion available in this runtime without an I2V service.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import subprocess
import tempfile
import time
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from imageio_ffmpeg import get_ffmpeg_exe

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references/characters/REF-CHAR-01-master-skier.png"
EXPECTED_SHA256 = "3b0bbeb5199e254930a9938f9dd1b2371c9fbbcb33311d1d6af494b9de4cc407"
DEFAULT_OUTPUT = ROOT / "video/tests/skier_motion_test_v1.mp4"
WIDTH, HEIGHT, FPS, DURATION = 1920, 1080, 24, 6.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def smooth(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def make_particles(seed: int = 41) -> list[tuple[float, float, float, float, float, int]]:
    rng = np.random.default_rng(seed)
    particles = []
    for _ in range(260):
        # x/y, radius, horizontal/vertical speed, opacity
        x = float(rng.uniform(-WIDTH, WIDTH))
        y = float(rng.uniform(-HEIGHT, HEIGHT))
        radius = float(rng.uniform(0.6, 3.6))
        vx = float(rng.uniform(-145, -38))
        vy = float(rng.uniform(14, 84))
        alpha = int(rng.uniform(24, 118))
        particles.append((x, y, radius, vx, vy, alpha))
    return particles


def frame_from_still(source: Image.Image, seconds: float, particles) -> Image.Image:
    progress = seconds / DURATION
    eased = smooth(progress)
    # One continuous, eased virtual camera move: a modest push with a small
    # downhill drift, never a cut, random shake, or uncontrolled zoom.
    zoom = 1.015 + 0.055 * eased
    center_x = 0.50 + 0.025 * eased
    center_y = 0.50 + 0.010 * eased
    crop_h = source.height / zoom
    crop_w = crop_h * WIDTH / HEIGHT
    cx = min(max(center_x * source.width, crop_w / 2), source.width - crop_w / 2)
    cy = min(max(center_y * source.height, crop_h / 2), source.height - crop_h / 2)
    image = source.crop((cx - crop_w / 2, cy - crop_h / 2,
                         cx + crop_w / 2, cy + crop_h / 2))
    frame = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    # Fine, depth-layered wind-driven snow moves independently of the locked
    # photo. Large foreground flakes receive short directional trails.
    fine = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    near = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    fine_draw, near_draw = ImageDraw.Draw(fine), ImageDraw.Draw(near)
    for x0, y0, radius, vx, vy, alpha in particles:
        x = (x0 + vx * seconds) % (WIDTH + 100) - 50
        y = (y0 + vy * seconds) % (HEIGHT + 100) - 50
        if radius < 2.4:
            fine_draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                              fill=(235, 244, 250, alpha))
        else:
            trail = min(18.0, 2.8 + abs(vx) * 0.055)
            near_draw.line((x, y, x - trail, y - trail * vy / max(abs(vx), 1.0)),
                           fill=(240, 247, 252, alpha), width=max(1, int(radius)))
            near_draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                              fill=(244, 248, 251, min(150, alpha + 24)))
    near = near.filter(ImageFilter.GaussianBlur(0.45))
    frame = Image.alpha_composite(frame.convert("RGBA"), fine)
    frame = Image.alpha_composite(frame, near).convert("RGB")

    # A faint, animated spindrift at ski level gives the test a moving
    # environment layer; the skier's pose remains exactly the source still.
    haze = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    haze_draw = ImageDraw.Draw(haze)
    phase = seconds * 1.35
    for n in range(9):
        x = int((780 + n * 120 - seconds * 96) % (WIDTH + 300) - 120)
        y = int(915 + 24 * math.sin(phase + n * 0.7))
        rx = 90 + n * 5
        haze_draw.ellipse((x - rx, y - 22, x + rx, y + 22),
                          fill=(238, 245, 248, 8))
    haze = haze.filter(ImageFilter.GaussianBlur(25))
    frame = Image.alpha_composite(frame.convert("RGBA"), haze).convert("RGB")
    return frame


def write_wind(path: Path) -> None:
    sample_rate = 48_000
    count = int(DURATION * sample_rate)
    rng = np.random.default_rng(7)
    white = rng.standard_normal(count).astype(np.float32)
    spectrum = np.fft.rfft(white)
    frequencies = np.fft.rfftfreq(count, 1 / sample_rate)
    shaping = (1 / np.sqrt(frequencies + 45.0)) * np.exp(-((frequencies / 950.0) ** 4))
    wind = np.fft.irfft(spectrum * shaping, n=count).astype(np.float32)
    rms = float(np.sqrt(np.mean(wind * wind)))
    wind /= max(rms, 1e-8)
    t = np.arange(count, dtype=np.float32) / sample_rate
    fade_in = np.clip(t / 0.6, 0, 1)
    fade_out = np.clip((DURATION - t) / 0.8, 0, 1)
    swell = 0.72 + 0.16 * np.sin(2 * np.pi * 0.22 * t)
    mono = np.clip(wind * fade_in * fade_out * swell * 0.055, -0.7, 0.7)
    stereo = np.column_stack((mono, mono * 0.93))
    pcm = (stereo * 32767).astype("<i2", copy=False)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = ROOT / output
    output = output.resolve()
    if not SOURCE.is_file() or sha256(SOURCE) != EXPECTED_SHA256:
        raise SystemExit("Locked REF-CHAR-01 hash mismatch; refusing to run the test.")
    if output.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite {output}; use --force explicitly.")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.stem + ".partial" + output.suffix)
    partial.unlink(missing_ok=True)

    source = Image.open(SOURCE).convert("RGB")
    if source.size != (1376, 768):
        raise SystemExit(f"Unexpected locked reference dimensions: {source.size}")
    particles = make_particles()
    ffmpeg = get_ffmpeg_exe()
    frame_count = int(DURATION * FPS)
    with tempfile.TemporaryDirectory(prefix="skier-motion-test-") as temp:
        wind_path = Path(temp) / "procedural_wind.wav"
        write_wind(wind_path)
        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}",
            "-framerate", str(FPS), "-i", "pipe:0", "-i", str(wind_path),
            "-map", "0:v:0", "-map", "1:a:0", "-t", str(DURATION),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "128k",
            "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
            "-metadata", "title=Skier motion capability test — programmatic still animation",
            "-metadata", "comment=Category C: camera move and procedural snow over unchanged REF-CHAR-01; no generated subject motion",
            str(partial),
        ]
        start = time.monotonic()
        with tempfile.TemporaryFile(mode="w+t") as log:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                       stderr=log, bufsize=0)
            assert process.stdin is not None
            try:
                for index in range(frame_count):
                    frame = frame_from_still(source, index / FPS, particles)
                    process.stdin.write(frame.tobytes())
                process.stdin.close()
                code = process.wait()
            except BrokenPipeError:
                process.stdin.close()
                code = process.wait()
            if code:
                log.seek(0)
                raise RuntimeError(f"FFmpeg test render failed: {log.read()}")

    # Decode end-to-end before preserving the test as a deliverable.
    check = subprocess.run([ffmpeg, "-hide_banner", "-v", "error", "-i", str(partial),
                            "-f", "null", "-"], capture_output=True, text=True)
    if check.returncode:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"Motion test failed decode verification: {check.stderr}")
    if output.exists():
        output.unlink()
    partial.replace(output)
    print(f"Method: C — programmatic camera movement and procedural snow over one locked still")
    print("AI-generated video / subject articulation: unavailable in this session; not claimed")
    print(f"Frames: {frame_count} at {FPS} fps; duration: {DURATION:.2f} s; resolution: {WIDTH}x{HEIGHT}")
    print(f"Source SHA-256: {sha256(SOURCE)}")
    print(f"Test: {output} ({output.stat().st_size:,} bytes)")
    print(f"Test SHA-256: {sha256(output)}")
    print(f"Verified decode; elapsed {time.monotonic() - start:.1f} s")
    metadata = subprocess.run([ffmpeg, "-hide_banner", "-i", str(output), "-map", "0:v:0",
                               "-frames:v", "1", "-f", "null", "-"],
                              capture_output=True, text=True)
    print(metadata.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
