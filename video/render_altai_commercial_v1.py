#!/usr/bin/env python3
"""Reproducibly assemble the Altai rehabilitation commercial from locked stills.

The source PNGs and approved Russian narration are read-only. Motion is 2D
Ken Burns-style reframing of still images; this script does not generate video
footage. It creates an original, deterministic synthetic score/ambience and
renders an H.264/AAC MP4 with FFmpeg from imageio-ffmpeg.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import subprocess
import sys
import tempfile
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from imageio_ffmpeg import get_ffmpeg_exe
except ImportError as exc:  # pragma: no cover - exercised on fresh installations
    raise SystemExit(
        "Missing render dependency. Install with: "
        "python -m pip install -r video/requirements.txt"
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, FPS = 1920, 1080, 24
TOTAL_SECONDS = 77.0
VOICEOVER = ROOT / "audio/voiceover/voiceover_ru_full_v1.mp3"
DEFAULT_OUTPUT = ROOT / "video/final/altai_rehabilitation_commercial_v1.mp4"

# SHA-256 pins protect every approved source used by this assembly. The files
# are never written to; any mismatch aborts the render rather than silently
# using an unreviewed replacement.
APPROVED_SOURCES = {
    "scene01": ("references/scenes/REF-SCENE-01-ski-descent.png", "384fd25d66cb3598939b0e8e8bb52e9b9019439f651b10bbbafef1ea224191dc"),
    "scene02": ("references/scenes/REF-SCENE-02-injury-aftermath-v2.png", "4b4e21eed7a5b62d368782c4c5b805f836e07fd1ac9ecba932bf3a6fd0ac5074"),
    "scene03": ("references/scenes/REF-SCENE-03-center-exterior-reveal.png", "3cff05af0b82055281a203e5187ac4a0266cd4f53d6b05440de280dc74543ac0"),
    "scene04": ("references/scenes/REF-SCENE-04-reception-welcome.png", "dcc6b97af2e1452d9a09a6bf5397ab1b8282a56c08aac864cecf9db7a6f00320"),
    "scene05": ("references/scenes/REF-SCENE-05-biomechanics-assessment-v2.png", "0a6d303ee25232ba9d82474e120001cbcf0c2813debdaf9ea44d3031f4722acb"),
    "scene06": ("references/scenes/REF-SCENE-06-rehabilitation-exercises.png", "d163d7baab6f34d2cc5720e3b68782adb7389b22a83af793c54fa442395ad9de"),
    "scene07": ("references/scenes/REF-SCENE-07-recovery-physiotherapy.png", "a3899eb7d0c1a5470c7fa90dc31e3760e3dd9dfc56e0ac519855911d542618e1"),
    "scene08": ("references/scenes/REF-SCENE-08-rehabilitation-team.png", "581c44ba71f91d3de5a0f3447246e3d406afa7427b99e60d95db6a5ba15ef749"),
    "scene09": ("references/scenes/REF-SCENE-09-return-to-slopes.png", "5eec2e8d9dc4730241c10500e2541b97da51475827d714b1c5f5e9ccb7626897"),
    "scene10": ("references/scenes/REF-SCENE-10-final-brand-card.png", "5c173731529dd1899046b842997d798865a2059062f0a6cec99696a9afdc7486"),
    "voiceover": ("audio/voiceover/voiceover_ru_full_v1.mp3", "7d5368d3075ba16c30e9f6bf717d477c1ff2c6eb51bf59dba2a86b6d199376f1"),
}


@dataclass(frozen=True)
class Shot:
    source: str
    seconds: float
    zoom: tuple[float, float]
    center: tuple[float, float, float, float]
    label: str


# Timeline follows editing/video_assembly_plan.md (20 beats / exactly 77 s).
# Repeated source stills use new editorial crops, not new footage.
SHOTS: tuple[Shot, ...] = (
    Shot("scene01", 4.0, (1.01, 1.045), (0.48, 0.50, 0.51, 0.51), "01 Altai descent — wide"),
    Shot("scene01", 4.0, (1.07, 1.14), (0.50, 0.50, 0.54, 0.51), "02 Descent — tighter reframe"),
    Shot("scene02", 3.0, (1.035, 1.085), (0.50, 0.50, 0.52, 0.48), "03 Off-screen fall — aftermath reveal"),
    Shot("scene02", 5.0, (1.085, 1.145), (0.52, 0.46, 0.53, 0.46), "04 Aftermath — restrained push"),
    Shot("scene03", 5.0, (1.01, 1.055), (0.50, 0.54, 0.52, 0.53), "05 Center exterior"),
    Shot("scene04", 4.0, (1.015, 1.06), (0.56, 0.51, 0.58, 0.50), "06 Reception welcome"),
    Shot("scene04", 3.0, (1.07, 1.115), (0.58, 0.48, 0.59, 0.47), "07 Reception — detail reframe"),
    Shot("scene05", 4.0, (1.01, 1.045), (0.54, 0.53, 0.55, 0.52), "08 Supervised movement — wide"),
    Shot("scene05", 3.0, (1.065, 1.11), (0.56, 0.52, 0.58, 0.51), "09 Movement — detail reframe"),
    Shot("scene06", 4.0, (1.015, 1.06), (0.55, 0.54, 0.57, 0.53), "10 Controlled rehabilitation exercise"),
    Shot("scene07", 4.0, (1.015, 1.06), (0.56, 0.52, 0.58, 0.51), "11 Supervised mobility"),
    Shot("scene07", 3.0, (1.065, 1.11), (0.59, 0.51, 0.61, 0.50), "12 Mobility — detail reframe"),
    Shot("scene08", 7.0, (1.01, 1.045), (0.56, 0.52, 0.58, 0.51), "13 Athlete and specialist"),
    Shot("scene08", 4.0, (1.055, 1.105), (0.58, 0.50, 0.60, 0.50), "14 Conversation — closer reframe"),
    Shot("scene09", 5.0, (1.01, 1.055), (0.49, 0.52, 0.51, 0.50), "15 Return to the slope — hero hold"),
    Shot("scene09", 5.0, (1.055, 1.12), (0.51, 0.52, 0.54, 0.51), "16 Return — second digital crop"),
    Shot("scene09", 4.0, (1.08, 1.22), (0.51, 0.55, 0.50, 0.40), "17 Simulated upward reframe — no footage"),
    Shot("scene10", 1.0, (1.0, 1.0), (0.50, 0.50, 0.50, 0.50), "18 Approved backup end card / motif"),
    Shot("scene10", 1.5, (1.0, 1.0), (0.50, 0.50, 0.50, 0.50), "19 Brand name"),
    Shot("scene10", 3.5, (1.0, 1.0), (0.50, 0.50, 0.50, 0.50), "20 Tagline and website"),
)

BRAND_NAME = "РЕАБИЛИТАЦИОННЫЙ ЦЕНТР АЛТАЙ"
TAGLINE = "Твой сезон продолжается."
WEBSITE = "altaysportreab.ru"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sources() -> dict[str, Path]:
    result: dict[str, Path] = {}
    for key, (relative, expected) in APPROVED_SOURCES.items():
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"Approved source is missing: {relative}")
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"Approved source hash mismatch for {relative}:\n"
                f"  expected {expected}\n  found    {actual}\n"
                "Refusing to render with a changed/ unapproved source."
            )
        result[key] = path
    return result


def ease01(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def shot_frame(source: Image.Image, shot: Shot, frame_in_shot: int) -> Image.Image:
    count = int(round(shot.seconds * FPS))
    progress = 0.0 if count <= 1 else frame_in_shot / (count - 1)
    eased = ease01(progress)
    zoom = shot.zoom[0] + (shot.zoom[1] - shot.zoom[0]) * eased
    cx0, cy0, cx1, cy1 = shot.center
    cx = (cx0 + (cx1 - cx0) * eased) * source.width
    cy = (cy0 + (cy1 - cy0) * eased) * source.height

    # Crop to 16:9 without distorting or rewriting the approved original.
    crop_h = source.height / zoom
    crop_w = crop_h * WIDTH / HEIGHT
    cx = min(max(cx, crop_w / 2), source.width - crop_w / 2)
    cy = min(max(cy, crop_h / 2), source.height - crop_h / 2)
    left = cx - crop_w / 2
    top = cy - crop_h / 2
    box = (left, top, left + crop_w, top + crop_h)
    return source.crop(box).resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def find_cyrillic_font() -> Path:
    candidates = (
        ROOT / "video/assets/DejaVuSans.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "A Cyrillic-capable sans-serif TTF font is required for the end card. "
        "Install DejaVu Sans or put video/assets/DejaVuSans.ttf in the project."
    )


def make_text_layer(text: str, font: ImageFont.FreeTypeFont, y: int) -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    # A very soft, warm shadow separates the typesetting from the reserved dark band.
    draw.text((WIDTH // 2, y + 2), text, font=font, anchor="mm", fill=(45, 38, 29, 115))
    draw.text((WIDTH // 2, y), text, font=font, anchor="mm", fill=(231, 216, 184, 255))
    return layer


def alpha_composite(base: Image.Image, layer: Image.Image, alpha: float) -> Image.Image:
    if alpha <= 0.0:
        return base
    if alpha >= 1.0:
        return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")
    overlay = layer.copy()
    overlay.putalpha(overlay.getchannel("A").point(lambda value: int(value * alpha)))
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")


def fade_to_color(frame: Image.Image, color: tuple[int, int, int], alpha: float) -> Image.Image:
    if alpha <= 0.0:
        return frame
    solid = Image.new("RGB", (WIDTH, HEIGHT), color)
    return Image.blend(frame, solid, min(1.0, max(0.0, alpha)))


def add_end_card_text(
    frame: Image.Image,
    global_seconds: float,
    title_layer: Image.Image,
    tagline_layer: Image.Image,
    website_layer: Image.Image,
) -> Image.Image:
    # Copy-only overlays; exact owner-approved strings are retained above.
    for layer, start, fade in (
        (title_layer, 72.0, 0.40),
        (tagline_layer, 73.5, 0.36),
        (website_layer, 74.3, 0.36),
    ):
        alpha = ease01((global_seconds - start) / fade)
        frame = alpha_composite(frame, layer, alpha)
    return frame


def _chord_notes() -> list[tuple[float, float, tuple[float, ...], float]]:
    # (start, end, notes in Hz, bass root in Hz). Neighboring pads overlap to
    # make an original slow harmonic bed without using an external recording.
    progression = [
        (0.0, 9.1, (146.83, 174.61, 220.00, 329.63), 73.42),       # Dm(add9)
        (7.0, 16.1, (116.54, 174.61, 220.00, 293.66), 58.27),      # Bbmaj7
        (14.0, 23.1, (130.81, 174.61, 196.00, 261.63), 87.31),     # F(add9)
        (21.0, 30.1, (130.81, 196.00, 293.66, 329.63), 65.41),     # C(add9)
        (28.0, 37.1, (146.83, 174.61, 220.00, 329.63), 73.42),
        (35.0, 44.1, (116.54, 174.61, 220.00, 293.66), 58.27),
        (42.0, 51.1, (130.81, 174.61, 196.00, 261.63), 87.31),
        (49.0, 58.1, (130.81, 196.00, 293.66, 329.63), 65.41),
        (56.0, 65.1, (146.83, 174.61, 220.00, 293.66), 73.42),
        (63.0, 72.1, (130.81, 174.61, 196.00, 261.63), 87.31),
        (70.0, 77.0, (130.81, 174.61, 220.00, 261.63), 87.31),
    ]
    return progression


def generate_audio_bed(path: Path, seconds: float = TOTAL_SECONDS, sample_rate: int = 48_000) -> None:
    """Write a deterministic original pad/pulse/wind bed as stereo PCM WAV."""
    count = int(round(seconds * sample_rate))
    rng = np.random.default_rng(20261028)
    left = np.zeros(count, dtype=np.float32)
    right = np.zeros(count, dtype=np.float32)
    sample_times = np.arange(count, dtype=np.float32) / sample_rate

    # Soft, slowly evolving chord pads with slightly detuned stereo voices.
    for chord_start, chord_end, notes, root in _chord_notes():
        first = max(0, int(chord_start * sample_rate))
        last = min(count, int(chord_end * sample_rate))
        if first >= last:
            continue
        t = np.arange(last - first, dtype=np.float32) / sample_rate
        attack = np.clip(t / 1.65, 0.0, 1.0)
        release = np.clip((chord_end - chord_start - t) / 1.9, 0.0, 1.0)
        envelope = (0.5 - 0.5 * np.cos(np.pi * attack)) * (0.5 - 0.5 * np.cos(np.pi * release))
        chord_level = 0.80 if chord_start < 21 else (0.93 if chord_start < 56 else 1.0)
        for frequency in notes:
            phase = float(rng.uniform(0, 2 * np.pi))
            detune_l = float(rng.uniform(-0.0022, -0.0008))
            detune_r = float(rng.uniform(0.0008, 0.0022))
            fundamental = np.float32(0.0155 * chord_level)
            harmonic = np.float32(0.0031 * chord_level)
            left_wave = (
                0.58 * np.sin(2 * np.pi * frequency * (1.0 + detune_l) * t + phase)
                + 0.42 * np.sin(2 * np.pi * frequency * (1.0 + detune_l * 0.65) * t + phase + 0.31)
                + 0.20 * np.sin(2 * np.pi * frequency * 2.0 * (1.0 + detune_l) * t + phase + 0.7)
            )
            right_wave = (
                0.58 * np.sin(2 * np.pi * frequency * (1.0 + detune_r) * t + phase + 0.12)
                + 0.42 * np.sin(2 * np.pi * frequency * (1.0 + detune_r * 0.65) * t + phase + 0.43)
                + 0.20 * np.sin(2 * np.pi * frequency * 2.0 * (1.0 + detune_r) * t + phase + 0.82)
            )
            left[first:last] += (fundamental * left_wave + harmonic * left_wave) * envelope
            right[first:last] += (fundamental * right_wave + harmonic * right_wave) * envelope

        # Very low sustained root under each chord; deliberately restrained.
        bass_gain = np.float32(0.012)
        bass_phase = float(rng.uniform(0, 2 * np.pi))
        bass_l = np.sin(2 * np.pi * root * t + bass_phase)
        bass_r = np.sin(2 * np.pi * root * 1.0015 * t + bass_phase + 0.15)
        bass_env = np.minimum(envelope, 0.75)
        left[first:last] += bass_gain * bass_l * bass_env
        right[first:last] += bass_gain * bass_r * bass_env

    # Sparse soft bell/pluck notes add a gentle melodic thread; no sampled track.
    motif = [
        (3.0, 440.00), (9.0, 587.33), (15.0, 523.25), (23.0, 392.00),
        (31.0, 440.00), (39.0, 523.25), (47.0, 587.33), (55.0, 493.88),
        (61.0, 587.33), (67.0, 523.25), (71.5, 440.00),
    ]
    for onset, frequency in motif:
        first = int(onset * sample_rate)
        length = min(int(1.65 * sample_rate), count - first)
        if length <= 0:
            continue
        t = np.arange(length, dtype=np.float32) / sample_rate
        attack = np.clip(t / 0.018, 0.0, 1.0)
        env = attack * np.exp(-t / 0.72)
        phase = float(rng.uniform(0, 2 * np.pi))
        note = 0.0105 * env * (
            np.sin(2 * np.pi * frequency * t + phase)
            + 0.20 * np.sin(2 * np.pi * frequency * 2.0 * t + phase + 0.2)
            + 0.05 * np.sin(2 * np.pi * frequency * 3.0 * t + phase + 0.4)
        )
        pan = 0.5 + 0.22 * math.sin(onset * 0.31)
        left[first:first + length] += note * math.sqrt(1.0 - pan)
        right[first:first + length] += note * math.sqrt(pan)

    # A quiet rounded pulse enters during the recovery build and opens on return.
    for onset in np.arange(30.0, 69.5, 2.0):
        first = int(onset * sample_rate)
        length = min(int(0.42 * sample_rate), count - first)
        if length <= 0:
            continue
        t = np.arange(length, dtype=np.float32) / sample_rate
        env = (1.0 - np.exp(-t / 0.012)) * np.exp(-t / 0.16)
        level = 0.0125 * (1.0 if onset < 57.0 else 1.12)
        pulse = level * env * np.sin(2 * np.pi * (58.0 + 4.0 * math.sin(onset)) * t)
        left[first:first + length] += pulse
        right[first:first + length] += pulse * 0.96

    # Pink-leaning, band-limited noise creates a soft alpine-air ambience.
    # Frequency-domain shaping is deterministic and avoids an external SFX file.
    white = rng.standard_normal(count).astype(np.float32)
    spectrum = np.fft.rfft(white)
    frequencies = np.fft.rfftfreq(count, 1.0 / sample_rate)
    pink = 1.0 / np.sqrt(frequencies + 35.0)
    highpass = 1.0 - np.exp(-((frequencies / 55.0) ** 2))
    lowpass = np.exp(-((frequencies / 750.0) ** 4))
    wind = np.fft.irfft(spectrum * pink * highpass * lowpass, n=count).astype(np.float32)
    wind_rms = float(np.sqrt(np.mean(wind * wind)))
    if wind_rms > 0:
        wind /= wind_rms

    wind_gate = np.zeros(count, dtype=np.float32)
    # Opening and return-to-slope air, with only a faint bed indoors.
    wind_keys = ((0.0, 0.72), (0.8, 0.80), (7.7, 0.80), (10.0, 0.48),
                 (16.0, 0.10), (54.0, 0.10), (57.0, 0.48), (60.0, 0.80),
                 (70.0, 0.72), (71.0, 0.34), (73.0, 0.0), (77.0, 0.0))
    wind_gate[:] = np.interp(sample_times, [p[0] for p in wind_keys], [p[1] for p in wind_keys])
    left += 0.018 * wind * wind_gate
    right += 0.016 * wind * wind_gate

    # Soft snow-brush / low thump at the implied off-screen transition (~8 s).
    impact_start = int(7.88 * sample_rate)
    impact_length = min(int(0.56 * sample_rate), count - impact_start)
    t = np.arange(impact_length, dtype=np.float32) / sample_rate
    impact_env = np.sin(np.pi * np.clip(t / (impact_length / sample_rate), 0.0, 1.0)) ** 1.4
    noise_slice = wind[impact_start:impact_start + impact_length]
    thud = 0.042 * np.exp(-t / 0.12) * np.sin(2 * np.pi * 58.0 * t)
    swish = 0.014 * noise_slice * impact_env
    impact = thud + swish
    left[impact_start:impact_start + impact_length] += impact
    right[impact_start:impact_start + impact_length] += impact * 0.92

    # Slow musical arc: restrained opening, warm build through recovery, clear
    # lift on the return, then a soft resolution under the clean brand card.
    gain_keys = ((0.0, 0.53), (2.0, 0.60), (12.0, 0.65), (21.0, 0.73),
                 (36.0, 0.82), (50.0, 0.88), (58.0, 0.98), (65.0, 1.0),
                 (70.0, 0.88), (73.0, 0.70), (77.0, 0.0))
    music_gain = np.interp(sample_times, [p[0] for p in gain_keys], [p[1] for p in gain_keys]).astype(np.float32)
    # A coherent global fader lets score, wind, and the accent enter and resolve
    # together; FFmpeg side-chain ducking keeps the entire bed below the VO.
    score_only_left = left.copy()
    score_only_right = right.copy()
    bed_gain = 2.2  # Lift the very restrained synth bed to a soft, audible level.
    left = score_only_left * music_gain * bed_gain
    right = score_only_right * music_gain * bed_gain

    stereo = np.column_stack((left, right))
    peak = float(np.max(np.abs(stereo)))
    if peak > 0.82:
        stereo *= 0.82 / peak
    pcm = np.clip(stereo * 32767.0, -32768, 32767).astype("<i2", copy=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def run_checked(command: list[str], *, stderr_target=None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=stderr_target if stderr_target is not None else subprocess.PIPE,
        check=True,
    )


def render(args: argparse.Namespace) -> None:
    approved = verify_sources()
    ffmpeg = get_ffmpeg_exe()
    version = run_checked([ffmpeg, "-hide_banner", "-version"]).stdout.splitlines()[0]
    encoders = run_checked([ffmpeg, "-hide_banner", "-encoders"]).stdout
    if "libx264" not in encoders:
        raise RuntimeError("The selected FFmpeg build does not include the required libx264 encoder.")

    font_path = find_cyrillic_font()
    font_name = ImageFont.truetype(str(font_path), 44)
    font_tagline = ImageFont.truetype(str(font_path), 44)
    font_url = ImageFont.truetype(str(font_path), 38)
    title_layer = make_text_layer(BRAND_NAME, font_name, 530)
    tagline_layer = make_text_layer(TAGLINE, font_tagline, 693)
    website_layer = make_text_layer(WEBSITE, font_url, 843)

    images: dict[str, Image.Image] = {
        key: Image.open(path).convert("RGB") for key, path in approved.items() if key.startswith("scene")
    }
    for key, image in images.items():
        if image.size != (1376, 768):
            raise RuntimeError(f"Unexpected locked image dimensions for {key}: {image.size}")

    shot_frames = [int(round(shot.seconds * FPS)) for shot in SHOTS]
    if sum(shot_frames) != int(round(TOTAL_SECONDS * FPS)):
        raise AssertionError("Timeline does not add up to exactly 77 seconds at 24 fps.")
    frame_total = sum(shot_frames)
    offsets: list[int] = []
    cursor = 0
    for frame_count in shot_frames:
        offsets.append(cursor)
        cursor += frame_count

    # Cache first frames used for cross-dissolves, keeping the transition work
    # deterministic and avoiding an extra render at each cut.
    first_frames = [shot_frame(images[shot.source], shot, 0) for shot in SHOTS]

    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = ROOT / output
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not args.force:
        raise FileExistsError(f"Refusing to overwrite existing output: {output}\nUse --force to replace it.")
    partial = output.with_name(output.stem + ".partial" + output.suffix)
    if partial.exists():
        partial.unlink()

    with tempfile.TemporaryDirectory(prefix="altai-commercial-render-") as temp_dir:
        music_path = Path(temp_dir) / "original_synthetic_score_and_ambience.wav"
        generate_audio_bed(music_path)

        filter_graph = (
            "[1:a]aresample=48000,asetpts=PTS-STARTPTS,"
            "pan=stereo|c0=c0|c1=c0,volume=0.98[voice];"
            "[2:a]aresample=48000,asetpts=PTS-STARTPTS,volume=1.0[bed];"
            "[voice]asplit=2[voice_mix][voice_key];"
            "[bed][voice_key]sidechaincompress=threshold=0.05:ratio=1.8:"
            "attack=60:release=500:makeup=1[ducked];"
            "[voice_mix][ducked]amix=inputs=2:duration=longest:"
            "dropout_transition=2:normalize=0,"
            "alimiter=limit=0.92:attack=5:release=60[aout]"
        )
        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pixel_format", "rgb24",
            "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", str(FPS), "-i", "pipe:0",
            "-i", str(VOICEOVER), "-i", str(music_path),
            "-filter_complex", filter_graph,
            "-map", "0:v:0", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-profile:v", "high", "-level:v", "4.1", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-fps_mode", "cfr",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-t", f"{TOTAL_SECONDS:.3f}", "-movflags", "+faststart",
            "-metadata", "title=Altai Rehabilitation Center — Return to the Slopes",
            "-metadata", "comment=2D animation of approved stills; no generated live-action footage",
            str(partial),
        ]
        print(f"Renderer: {version}")
        print(f"Font: {font_path}")
        print(f"Encoding {frame_total} frames ({TOTAL_SECONDS:.1f} s), {WIDTH}x{HEIGHT} at {FPS} fps …", flush=True)
        start_time = time.monotonic()
        with tempfile.TemporaryFile(mode="w+t") as ffmpeg_log:
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=ffmpeg_log,
                bufsize=0,
            )
            assert process.stdin is not None
            written = 0
            try:
                for shot_index, shot in enumerate(SHOTS):
                    for local_frame in range(shot_frames[shot_index]):
                        global_frame = offsets[shot_index] + local_frame
                        seconds = global_frame / FPS
                        frame = shot_frame(images[shot.source], shot, local_frame)

                        # The plan calls for a brief snow-white dip before the
                        # non-graphic aftermath; this is a transition, not a fall clip.
                        if shot_index == 1:
                            remaining = shot.seconds - local_frame / FPS
                            if remaining < 0.20:
                                frame = fade_to_color(frame, (245, 247, 247), 0.82 * (1.0 - remaining / 0.20))
                        elif shot_index == 2 and seconds < offsets[shot_index] / FPS + 0.24:
                            local_seconds = local_frame / FPS
                            frame = fade_to_color(frame, (245, 247, 247), 0.78 * (1.0 - ease01(local_seconds / 0.24)))

                        # Exterior-to-reception match dissolve (last 0.60 s of shot 5).
                        if shot_index == 4:
                            remaining = shot.seconds - local_frame / FPS
                            if remaining < 0.60:
                                alpha = ease01((0.60 - remaining) / 0.60)
                                frame = Image.blend(frame, first_frames[5], alpha)

                        # Scene 9 fallback reframe to the approved Scene 10 backup card.
                        if shot_index == 16:
                            remaining = shot.seconds - local_frame / FPS
                            if remaining < 0.78:
                                alpha = ease01((0.78 - remaining) / 0.78)
                                frame = Image.blend(frame, first_frames[17], alpha)

                        if shot_index >= 17:
                            frame = add_end_card_text(frame, seconds, title_layer, tagline_layer, website_layer)

                        # Gentle open and close; the card remains readable until its final fade.
                        if seconds < 0.62:
                            frame = fade_to_color(frame, (0, 0, 0), 1.0 - ease01(seconds / 0.62))
                        if seconds > TOTAL_SECONDS - 0.55:
                            frame = fade_to_color(frame, (0, 0, 0), ease01((seconds - (TOTAL_SECONDS - 0.55)) / 0.55))

                        process.stdin.write(frame.tobytes())
                        written += 1
                        if written % (FPS * 8) == 0:
                            elapsed = time.monotonic() - start_time
                            print(f"  {written:4d}/{frame_total} frames ({seconds:5.1f}s) — {elapsed:.0f}s elapsed", flush=True)
                process.stdin.close()
                return_code = process.wait()
            except BrokenPipeError:
                process.stdin.close()
                return_code = process.wait()
            if return_code != 0:
                ffmpeg_log.seek(0)
                detail = ffmpeg_log.read()
                raise RuntimeError(f"FFmpeg render failed (exit {return_code}):\n{detail}")

        if not partial.is_file() or partial.stat().st_size < 100_000:
            raise RuntimeError("FFmpeg returned success but the MP4 output is missing or unexpectedly small.")

        # Decode the entire export once before publishing it as the requested file.
        check = subprocess.run(
            [ffmpeg, "-hide_banner", "-v", "error", "-i", str(partial), "-f", "null", "-"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if check.returncode != 0:
            raise RuntimeError(f"The rendered MP4 did not decode cleanly:\n{check.stderr}")

    # Re-check locked source hashes after rendering, then atomically publish.
    verify_sources()
    if output.exists() and args.force:
        output.unlink()
    partial.replace(output)
    print(f"Verified playable MP4: {output}")
    print(f"File size: {output.stat().st_size:,} bytes")
    print(f"SHA-256: {sha256(output)}")
    print("Container metadata probe:")
    probe = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(output), "-map", "0:v:0", "-frames:v", "1", "-f", "null", "-"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(probe.stderr.strip())
    print(f"Elapsed: {time.monotonic() - start_time:.1f} seconds")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", default=str(DEFAULT_OUTPUT),
        help=f"MP4 output path (default: {DEFAULT_OUTPUT.relative_to(ROOT)})",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="replace an existing output file; source reference assets remain protected by hashes",
    )
    parser.add_argument(
        "--verify-only", action="store_true",
        help="check approved input hashes, font, FFmpeg and libx264 without rendering",
    )
    args = parser.parse_args(argv)

    try:
        verify_sources()
        if args.verify_only:
            ffmpeg = get_ffmpeg_exe()
            version = run_checked([ffmpeg, "-hide_banner", "-version"]).stdout.splitlines()[0]
            encoders = run_checked([ffmpeg, "-hide_banner", "-encoders"]).stdout
            if "libx264" not in encoders:
                raise RuntimeError("The selected FFmpeg build does not include libx264.")
            print(f"Approved source hashes: OK ({len(APPROVED_SOURCES)} files)")
            print(f"Cyrillic font: {find_cyrillic_font()}")
            print(f"FFmpeg: {version}")
            print("H.264 encoder: libx264 available")
            print(f"Timeline: {sum(s.seconds for s in SHOTS):.1f} s, {sum(int(round(s.seconds * FPS)) for s in SHOTS)} frames")
            return 0
        render(args)
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
