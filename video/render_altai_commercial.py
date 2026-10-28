#!/usr/bin/env python3
"""Director's-cut v2 assembly for RETURN TO THE SLOPE.

This renderer combines approved locked stills, three new provisional AI-made
STILLS (fall keyframe, assisted arrival, mountain end-card plate), procedural
snow/breath/impact overlays, smooth 2D camera paths, original synthetic audio,
and the unchanged approved Russian VO. It does NOT generate moving-image
footage or animate the skier's joints. All motion provenance is described in
video/README.md and the director's render log.
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

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from imageio_ffmpeg import get_ffmpeg_exe

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, FPS = 1920, 1080, 24
DURATION = 77.0
VOICEOVER = ROOT / "audio/voiceover/voiceover_ru_full_v1.mp3"
DEFAULT_OUTPUT = ROOT / "video/final/altai_rehabilitation_commercial_v2.mp4"

# Approved, locked material is hash-pinned and opened read-only. New stills are
# separately pinned for reproducibility but remain provisional/not approved.
SOURCE_HASHES = {
    "scene01": ("references/scenes/REF-SCENE-01-ski-descent.png", "384fd25d66cb3598939b0e8e8bb52e9b9019439f651b10bbbafef1ea224191dc"),
    "scene02": ("references/scenes/REF-SCENE-02-injury-aftermath-v2.png", "4b4e21eed7a5b62d368782c4c5b805f836e07fd1ac9ecba932bf3a6fd0ac5074"),
    "scene03": ("references/scenes/REF-SCENE-03-center-exterior-reveal.png", "3cff05af0b82055281a203e5187ac4a0266cd4f53d6b05440de280dc74543ac0"),
    "scene04": ("references/scenes/REF-SCENE-04-reception-welcome.png", "dcc6b97af2e1452d9a09a6bf5397ab1b8282a56c08aac864cecf9db7a6f00320"),
    "scene05": ("references/scenes/REF-SCENE-05-biomechanics-assessment-v2.png", "0a6d303ee25232ba9d82474e120001cbcf0c2813debdaf9ea44d3031f4722acb"),
    "scene06": ("references/scenes/REF-SCENE-06-rehabilitation-exercises.png", "d163d7baab6f34d2cc5720e3b68782adb7389b22a83af793c54fa442395ad9de"),
    "scene07": ("references/scenes/REF-SCENE-07-recovery-physiotherapy.png", "a3899eb7d0c1a5470c7fa90dc31e3760e3dd9dfc56e0ac519855911d542618e1"),
    "scene08": ("references/scenes/REF-SCENE-08-rehabilitation-team.png", "581c44ba71f91d3de5a0f3447246e3d406afa7427b99e60d95db6a5ba15ef749"),
    "scene09": ("references/scenes/REF-SCENE-09-return-to-slopes.png", "5eec2e8d9dc4730241c10500e2541b97da51475827d714b1c5f5e9ccb7626897"),
    "voiceover": ("audio/voiceover/voiceover_ru_full_v1.mp3", "7d5368d3075ba16c30e9f6bf717d477c1ff2c6eb51bf59dba2a86b6d199376f1"),
    "fall_keyframe": ("video/assets/skier_loss_of_control_keyframe_v1.png", "869924435d75bc045be03a1a57060aa744b3a81e8b532be4dd08d0c54cc11918"),
    "assisted_arrival": ("video/assets/assisted_arrival_keyframe_v1.png", "d491fc559021a6bd55e88f494a0443b0e1e35b2a78477df1661f42dc6d147895"),
    "endcard_landscape": ("video/assets/endcard_altai_landscape_v1.png", "2beca354122fe5ffac84b43c1ddd27e06be63db3fa37a172fc8b28d060061e5c"),
}


@dataclass(frozen=True)
class Shot:
    source: str
    seconds: float
    zoom: tuple[float, float]
    center: tuple[float, float, float, float]
    fx: str
    tone: str = "neutral"
    xfade_in: float = 0.0
    roll_degrees: float = 0.0
    label: str = ""


# Revised 21-beat director's timeline. Adjacent ski/recovery inserts use
# continuous camera endpoints; short dissolves are only used for motivated
# location/temperature transitions. The sum is exactly 77 s.
SHOTS: tuple[Shot, ...] = (
    Shot("scene01", 4.0, (1.005, 1.035), (0.48, 0.50, 0.51, 0.51), "ski", "cold", 0.0, 0.0, "wide Altai descent"),
    Shot("scene01", 3.0, (1.035, 1.11), (0.51, 0.51, 0.55, 0.50), "ski", "cold", 0.0, 0.0, "tracked carve"),
    Shot("fall_keyframe", 1.5, (1.015, 1.14), (0.52, 0.53, 0.53, 0.49), "fall", "cold", 0.18, -2.2, "AI still keyframe: loss of edge"),
    Shot("scene02", 0.6, (1.11, 1.115), (0.53, 0.45, 0.53, 0.45), "impact_reveal", "cold", 0.0, 0.0, "snow-white impact / reveal aftermath"),
    Shot("scene02", 4.9, (1.115, 1.18), (0.53, 0.45, 0.54, 0.44), "aftermath", "cold", 0.0, 0.0, "disorientation and breath"),
    Shot("scene03", 3.0, (1.005, 1.045), (0.50, 0.54, 0.51, 0.53), "exterior", "cold", 0.38, 0.0, "center exterior"),
    Shot("assisted_arrival", 4.0, (1.005, 1.055), (0.52, 0.53, 0.54, 0.51), "arrival", "neutral", 0.30, 0.0, "AI still: supported arrival"),
    Shot("scene04", 3.0, (1.01, 1.055), (0.55, 0.51, 0.58, 0.50), "reception", "warm", 0.42, 0.0, "welcome inside"),
    Shot("scene05", 4.0, (1.005, 1.055), (0.54, 0.53, 0.56, 0.52), "rehab", "warm", 0.26, 0.0, "assessment — medium"),
    Shot("scene07", 4.0, (1.01, 1.07), (0.56, 0.52, 0.58, 0.50), "rehab", "warm", 0.26, 0.0, "first mobility — measured"),
    Shot("scene06", 4.0, (1.01, 1.065), (0.54, 0.54, 0.56, 0.53), "rehab", "warm", 0.22, 0.0, "controlled split squat"),
    Shot("scene06", 3.0, (1.065, 1.12), (0.56, 0.53, 0.57, 0.52), "rehab_detail", "warm", 0.0, 0.0, "effort detail — continuous reframe"),
    Shot("scene07", 4.0, (1.01, 1.06), (0.56, 0.52, 0.58, 0.51), "rehab", "warm", 0.22, 0.0, "guided knee mobility"),
    Shot("scene07", 3.0, (1.06, 1.12), (0.58, 0.51, 0.60, 0.50), "rehab_detail", "warm", 0.0, 0.0, "specialist guidance detail"),
    Shot("scene08", 5.0, (1.005, 1.045), (0.56, 0.52, 0.58, 0.51), "team", "warm", 0.26, 0.0, "team — calm two-shot"),
    Shot("scene08", 4.0, (1.045, 1.10), (0.58, 0.51, 0.60, 0.50), "team_detail", "warm", 0.0, 0.0, "listening and confidence"),
    Shot("scene05", 4.0, (1.015, 1.075), (0.55, 0.52, 0.57, 0.51), "rehab", "warm", 0.22, 0.0, "progress check"),
    Shot("scene06", 4.0, (1.04, 1.10), (0.56, 0.53, 0.58, 0.52), "rehab", "warm", 0.22, 0.0, "growing confidence"),
    Shot("scene09", 5.0, (1.005, 1.075), (0.49, 0.52, 0.52, 0.50), "return", "cold", 0.42, 0.0, "return carve — hero"),
    Shot("scene09", 3.0, (1.075, 1.22), (0.52, 0.50, 0.50, 0.40), "sky_rise", "cold", 0.0, 0.0, "simulated rise to mountain sky"),
    Shot("endcard_landscape", 6.0, (1.02, 1.22), (0.50, 0.57, 0.50, 0.40), "endcard", "end", 0.55, 0.0, "typographic end card / digital camera rise"),
)

BRAND_NAME = "РЕАБИЛИТАЦИОННЫЙ ЦЕНТР АЛТАЙ"
TAGLINE = "Твой сезон продолжается."
WEBSITE = "altaysportreab.ru"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sources() -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for key, (relative, expected) in SOURCE_HASHES.items():
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"Required source is missing: {relative}")
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"Hash mismatch for {relative}: expected {expected}, got {actual}. "
                "Refusing to render with changed source material."
            )
        paths[key] = path
    return paths


def ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def crop_camera(source: Image.Image, shot: Shot, local_seconds: float) -> Image.Image:
    progress = 1.0 if shot.seconds <= 0 else max(0.0, min(1.0, local_seconds / shot.seconds))
    eased = ease(progress)
    zoom = shot.zoom[0] + (shot.zoom[1] - shot.zoom[0]) * eased
    cx0, cy0, cx1, cy1 = shot.center
    cx = (cx0 + (cx1 - cx0) * eased) * source.width
    cy = (cy0 + (cy1 - cy0) * eased) * source.height
    crop_h = source.height / zoom
    crop_w = crop_h * WIDTH / HEIGHT
    cx = min(max(cx, crop_w / 2), source.width - crop_w / 2)
    cy = min(max(cy, crop_h / 2), source.height - crop_h / 2)
    box = (cx - crop_w / 2, cy - crop_h / 2, cx + crop_w / 2, cy + crop_h / 2)
    frame = source.crop(box).resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    if shot.roll_degrees:
        angle = shot.roll_degrees * ease(progress)
        frame = frame.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False,
                             fillcolor=(222, 232, 239))
    return frame


def tint(frame: Image.Image, tone: str) -> Image.Image:
    colors = {
        "cold": ((137, 168, 193), 0.045),
        "neutral": ((228, 224, 211), 0.018),
        "warm": ((255, 213, 163), 0.043),
        "end": ((255, 239, 208), 0.012),
    }
    color, amount = colors.get(tone, ((255, 255, 255), 0.0))
    if amount <= 0:
        return frame
    return Image.blend(frame, Image.new("RGB", frame.size, color), amount)


def make_snow(seed: int = 2604) -> list[tuple[float, float, float, float, float, int]]:
    rng = np.random.default_rng(seed)
    particles = []
    for _ in range(300):
        particles.append((
            float(rng.uniform(-WIDTH, 2 * WIDTH)),
            float(rng.uniform(-HEIGHT, 2 * HEIGHT)),
            float(rng.uniform(0.6, 3.4)),
            float(rng.uniform(-145.0, -35.0)),
            float(rng.uniform(18.0, 96.0)),
            int(rng.uniform(28, 116)),
        ))
    return particles


def overlay_snow(frame: Image.Image, seconds: float, particles, density: int, intensity: float = 1.0) -> Image.Image:
    if density <= 0 or intensity <= 0:
        return frame
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for x0, y0, radius, vx, vy, alpha in particles[:density]:
        x = (x0 + vx * seconds) % (WIDTH + 100) - 50
        y = (y0 + vy * seconds) % (HEIGHT + 100) - 50
        a = int(alpha * intensity)
        if radius < 2.2:
            draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                         fill=(241, 247, 251, a))
        else:
            trail = min(17.0, 3.0 + abs(vx) * 0.055)
            draw.line((x, y, x - trail, y - trail * vy / max(abs(vx), 1.0)),
                      fill=(241, 247, 251, a), width=max(1, int(radius)))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                         fill=(245, 249, 252, min(160, a + 20)))
    layer = layer.filter(ImageFilter.GaussianBlur(0.32))
    return Image.alpha_composite(frame.convert("RGBA"), layer).convert("RGB")


def overlay_fall_burst(frame: Image.Image, local_seconds: float) -> Image.Image:
    age = local_seconds - 0.68
    if age < 0 or age > 0.64:
        return frame
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    weight = max(0.0, 1.0 - age / 0.64)
    # A directional powder burst around the ski-contact area. It is an FX layer,
    # not a substitute for articulated body motion.
    for i in range(56):
        angle = (i / 56.0) * 2 * math.pi
        speed = 105 + (i % 9) * 17
        x = 935 + math.cos(angle) * speed * age
        y = 870 + math.sin(angle) * speed * age - 140 * age
        radius = 2 + (i % 4) * 1.5
        alpha = int(92 * weight)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                     fill=(245, 250, 252, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(1.2))
    return Image.alpha_composite(frame.convert("RGBA"), layer).convert("RGB")


def overlay_breath(frame: Image.Image, local_seconds: float) -> Image.Image:
    # Two understated procedural breath puffs during the cold aftermath. This is
    # designed atmosphere, not generated facial movement or a medical cue.
    pulses = []
    for onset in (0.55, 2.05):
        age = local_seconds - onset
        if 0 <= age <= 0.75:
            pulses.append((age, max(0.0, math.sin(math.pi * age / 0.75))))
    if not pulses:
        return frame
    haze = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(haze)
    for age, strength in pulses:
        cx = int(965 + 20 * age)
        cy = int(238 - 18 * age)
        alpha = int(22 * strength)
        draw.ellipse((cx - 38, cy - 18, cx + 55, cy + 20), fill=(230, 239, 245, alpha))
        draw.ellipse((cx + 5, cy - 28, cx + 84, cy + 18), fill=(235, 242, 247, alpha // 2))
    haze = haze.filter(ImageFilter.GaussianBlur(17))
    return Image.alpha_composite(frame.convert("RGBA"), haze).convert("RGB")


def find_font_paths() -> tuple[Path, Path]:
    serif_candidates = (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"),
        ROOT / "video/assets/DejaVuSerif.ttf",
    )
    sans_candidates = (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        ROOT / "video/assets/DejaVuSans.ttf",
    )
    serif = next((p for p in serif_candidates if p.is_file()), None)
    sans = next((p for p in sans_candidates if p.is_file()), None)
    if not serif or not sans:
        raise FileNotFoundError("Install a Cyrillic-capable DejaVu Serif and Sans font for the end card.")
    return serif, sans


def draw_tracking_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
                       center: float, y: float, tracking: float, fill, anchor: str = "mm") -> None:
    widths = [float(font.getlength(ch)) for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x = center - total / 2
    for character, width in zip(text, widths):
        draw.text((x + width / 2, y), character, font=font, anchor=anchor, fill=fill)
        x += width + tracking


def make_endcard_layers(serif_path: Path, sans_path: Path) -> tuple[Image.Image, Image.Image, Image.Image]:
    # Supersampled, carefully tracked rendered type on transparent layers. No
    # fixed rectangles and no invented emblem/official logo are used.
    scale = 3
    size = (WIDTH * scale, HEIGHT * scale)
    title_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    tag_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    url_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    title_draw = ImageDraw.Draw(title_layer)
    tag_draw = ImageDraw.Draw(tag_layer)
    url_draw = ImageDraw.Draw(url_layer)

    accent = (179, 145, 88, 205)
    title_color = (29, 45, 54, 255)
    tagline_color = (37, 53, 61, 250)
    url_color = (44, 62, 69, 240)

    title_font = ImageFont.truetype(str(serif_path), 43 * scale)
    tagline_font = ImageFont.truetype(str(serif_path), 47 * scale)
    url_font = ImageFont.truetype(str(sans_path), 25 * scale)

    # Minimal hairline and point are typographic rules, not a brand mark.
    center = WIDTH * scale / 2
    title_draw.line((center - 95 * scale, 248 * scale, center + 95 * scale, 248 * scale),
                    fill=accent, width=2 * scale)
    title_draw.ellipse((center - 2.2 * scale, 245.8 * scale,
                        center + 2.2 * scale, 250.2 * scale), fill=accent)
    draw_tracking_text(title_draw, BRAND_NAME, title_font, center, 332 * scale,
                       2.6 * scale, title_color)
    draw_tracking_text(tag_draw, TAGLINE, tagline_font, center, 414 * scale,
                       0.8 * scale, tagline_color)
    draw_tracking_text(url_draw, WEBSITE, url_font, center, 490 * scale,
                       3.2 * scale, url_color)

    resample = Image.Resampling.LANCZOS
    return (title_layer.resize((WIDTH, HEIGHT), resample),
            tag_layer.resize((WIDTH, HEIGHT), resample),
            url_layer.resize((WIDTH, HEIGHT), resample))


def composite_layer(frame: Image.Image, layer: Image.Image, alpha: float, dy: int = 0) -> Image.Image:
    alpha = max(0.0, min(1.0, alpha))
    if alpha <= 0:
        return frame
    overlay = layer.copy()
    if dy:
        translated = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
        translated.alpha_composite(overlay, (0, dy))
        overlay = translated
    if alpha < 1:
        overlay.putalpha(overlay.getchannel("A").point(lambda value: int(value * alpha)))
    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")


def add_endcard_type(frame: Image.Image, global_seconds: float, layers) -> Image.Image:
    name, tagline, url = layers
    # Sequential, restrained reveals; hold the full message legibly to picture end.
    for layer, start, fade in (
        (name, 72.0, 0.80),
        (tagline, 73.20, 0.72),
        (url, 74.35, 0.72),
    ):
        alpha = ease((global_seconds - start) / fade)
        frame = composite_layer(frame, layer, alpha, dy=int((1 - alpha) * 8))
    return frame


def shaped_noise(count: int, sample_rate: int, rng, low: float, high: float, pink: bool = True) -> np.ndarray:
    white = rng.standard_normal(count).astype(np.float32)
    spectrum = np.fft.rfft(white)
    del white
    frequencies = np.fft.rfftfreq(count, 1.0 / sample_rate)
    if pink:
        tilt = 1.0 / np.sqrt(frequencies + max(8.0, low * 0.35))
    else:
        tilt = np.ones_like(frequencies)
    highpass = 1.0 - np.exp(-((frequencies / max(low, 1.0)) ** 2))
    lowpass = np.exp(-((frequencies / max(high, 10.0)) ** 4))
    shaped = np.fft.irfft(spectrum * tilt * highpass * lowpass, n=count).astype(np.float32)
    del spectrum, frequencies, tilt, highpass, lowpass
    rms = float(np.sqrt(np.mean(shaped * shaped)))
    if rms > 1e-9:
        shaped /= rms
    return shaped


def chord_progression() -> list[tuple[float, float, tuple[float, ...], float]]:
    return [
        (0.0, 9.2, (146.83, 174.61, 220.00, 329.63), 73.42),
        (7.3, 16.4, (116.54, 174.61, 220.00, 293.66), 58.27),
        (14.6, 23.7, (130.81, 174.61, 196.00, 261.63), 87.31),
        (21.9, 31.0, (130.81, 196.00, 293.66, 329.63), 65.41),
        (29.2, 38.3, (146.83, 174.61, 220.00, 329.63), 73.42),
        (36.5, 45.6, (116.54, 174.61, 220.00, 293.66), 58.27),
        (43.8, 52.9, (130.81, 174.61, 196.00, 261.63), 87.31),
        (51.1, 60.2, (130.81, 196.00, 293.66, 329.63), 65.41),
        (58.4, 67.5, (146.83, 174.61, 220.00, 293.66), 73.42),
        (65.7, 74.8, (130.81, 174.61, 196.00, 261.63), 87.31),
        (72.5, 77.0, (130.81, 174.61, 220.00, 261.63), 87.31),
    ]


def write_score_bed(path: Path, seconds: float = DURATION, sample_rate: int = 48_000) -> None:
    """Compose an original, deterministic synthetic score and designed ambience."""
    count = int(round(seconds * sample_rate))
    rng = np.random.default_rng(28102026)
    time_axis = np.arange(count, dtype=np.float32) / sample_rate
    music_l = np.zeros(count, dtype=np.float32)
    music_r = np.zeros(count, dtype=np.float32)

    # Slow, warm harmonic bed with detuned stereo partials and soft bass roots.
    for start, end, notes, root in chord_progression():
        first = max(0, int(start * sample_rate))
        last = min(count, int(end * sample_rate))
        if last <= first:
            continue
        t = np.arange(last - first, dtype=np.float32) / sample_rate
        attack = np.clip(t / 1.45, 0.0, 1.0)
        release = np.clip((end - start - t) / 1.65, 0.0, 1.0)
        envelope = (0.5 - 0.5 * np.cos(np.pi * attack)) * (0.5 - 0.5 * np.cos(np.pi * release))
        for frequency in notes:
            phase = float(rng.uniform(0, 2 * np.pi))
            detune_l = float(rng.uniform(-0.0021, -0.0008))
            detune_r = float(rng.uniform(0.0008, 0.0021))
            left_wave = (0.62 * np.sin(2 * np.pi * frequency * (1 + detune_l) * t + phase)
                         + 0.38 * np.sin(2 * np.pi * frequency * 1.004 * t + phase + 0.35)
                         + 0.17 * np.sin(2 * np.pi * frequency * 2 * t + phase + 0.6))
            right_wave = (0.62 * np.sin(2 * np.pi * frequency * (1 + detune_r) * t + phase + 0.12)
                          + 0.38 * np.sin(2 * np.pi * frequency * 0.996 * t + phase + 0.48)
                          + 0.17 * np.sin(2 * np.pi * frequency * 2 * t + phase + 0.8))
            music_l[first:last] += 0.0175 * left_wave * envelope
            music_r[first:last] += 0.0175 * right_wave * envelope
        bass_phase = float(rng.uniform(0, 2 * np.pi))
        bass_env = np.minimum(envelope, 0.72)
        music_l[first:last] += 0.010 * np.sin(2 * np.pi * root * t + bass_phase) * bass_env
        music_r[first:last] += 0.010 * np.sin(2 * np.pi * root * 1.0015 * t + bass_phase + 0.15) * bass_env

    # Sparse high, soft plucks; a pulse gradually enters with the recovery montage.
    for onset, frequency in ((3, 440), (11, 587.33), (18, 523.25), (26, 392),
                             (34, 440), (42, 523.25), (50, 587.33), (58, 493.88),
                             (64, 587.33), (69, 523.25), (73, 440)):
        first = int(onset * sample_rate)
        length = min(int(1.25 * sample_rate), count - first)
        t = np.arange(length, dtype=np.float32) / sample_rate
        env = (1.0 - np.exp(-t / 0.018)) * np.exp(-t / 0.54)
        phase = float(rng.uniform(0, 2 * np.pi))
        pluck = 0.0068 * env * (np.sin(2 * np.pi * frequency * t + phase)
                                + 0.17 * np.sin(2 * np.pi * frequency * 2 * t + phase + 0.2))
        pan = 0.5 + 0.18 * math.sin(onset * 0.3)
        music_l[first:first + length] += pluck * math.sqrt(1.0 - pan)
        music_r[first:first + length] += pluck * math.sqrt(pan)

    pulse_curve = np.interp(time_axis, [0, 24, 34, 52, 62, 70, 77], [0, 0.0, 0.35, 0.65, 1.0, 0.75, 0.0])
    for onset in np.arange(28.0, 70.0, 1.8):
        first = int(onset * sample_rate)
        length = min(int(0.38 * sample_rate), count - first)
        t = np.arange(length, dtype=np.float32) / sample_rate
        env = (1.0 - np.exp(-t / 0.012)) * np.exp(-t / 0.14)
        index = min(count - 1, first)
        level = 0.011 * float(pulse_curve[index])
        freq = 54.0 + 4.0 * math.sin(onset * 0.45)
        thump = level * env * np.sin(2 * np.pi * freq * t)
        music_l[first:first + length] += thump
        music_r[first:first + length] += thump * 0.96

    music_gain_keys = ((0.0, 0.36), (4.0, 0.45), (7.6, 0.52), (8.4, 0.18),
                       (8.8, 0.025), (10.6, 0.028), (11.4, 0.16), (14.0, 0.34),
                       (21.0, 0.48), (30.0, 0.62), (43.0, 0.72), (54.0, 0.80),
                       (60.0, 0.96), (66.0, 1.08), (71.0, 0.92), (74.0, 0.83), (77.0, 0.0))
    music_gain = np.interp(time_axis, [p[0] for p in music_gain_keys], [p[1] for p in music_gain_keys]).astype(np.float32)
    music_l *= music_gain
    music_r *= music_gain

    # Alpine wind, shaped scrape/edge texture, and a controlled snow impact.
    wind = shaped_noise(count, sample_rate, rng, low=38.0, high=820.0, pink=True)
    wind_keys = ((0.0, 0.72), (1.0, 0.86), (6.5, 0.78), (7.8, 0.95), (8.5, 0.07),
                 (10.8, 0.035), (13.0, 0.25), (16.0, 0.16), (20.8, 0.04),
                 (55.0, 0.04), (60.0, 0.18), (63.0, 0.55), (68.0, 0.86),
                 (71.0, 0.55), (74.0, 0.26), (77.0, 0.0))
    wind_gain = np.interp(time_axis, [p[0] for p in wind_keys], [p[1] for p in wind_keys]).astype(np.float32)
    wind_mod = 0.78 + 0.22 * np.sin(2 * np.pi * 0.11 * time_axis + 0.4)
    wind_l = 0.043 * wind * wind_gain * wind_mod
    wind_r = 0.039 * wind * wind_gain * (0.82 + 0.18 * np.sin(2 * np.pi * 0.09 * time_axis + 1.1))
    del wind

    scrape = shaped_noise(count, sample_rate, rng, low=240.0, high=3300.0, pink=False)
    ski_keys = ((0.0, 0.32), (1.0, 0.56), (3.4, 0.50), (4.0, 0.75), (6.6, 0.82),
                (7.2, 0.90), (7.8, 0.70), (8.15, 0.12), (8.5, 0.0),
                (61.0, 0.0), (63.0, 0.45), (65.0, 0.86), (68.0, 0.75),
                (70.5, 0.34), (71.5, 0.0), (77.0, 0.0))
    ski_gain = np.interp(time_axis, [p[0] for p in ski_keys], [p[1] for p in ski_keys]).astype(np.float32)
    scrape_mod = 0.68 + 0.32 * np.sin(2 * np.pi * 0.7 * time_axis + 0.6)
    ski_l = 0.021 * scrape * ski_gain * scrape_mod
    ski_r = 0.018 * scrape * ski_gain * (0.75 + 0.25 * np.sin(2 * np.pi * 0.58 * time_axis + 1.3))
    del scrape

    # Muted off-screen impact at 8.2 s, followed by a near-silent bed.
    impact_start = int(8.18 * sample_rate)
    impact_len = int(0.55 * sample_rate)
    it = np.arange(impact_len, dtype=np.float32) / sample_rate
    impact_env = np.exp(-it / 0.15) * (1.0 - np.exp(-it / 0.012))
    impact_noise = rng.standard_normal(impact_len).astype(np.float32)
    thud = 0.050 * impact_env * np.sin(2 * np.pi * 59.0 * it)
    snow = 0.012 * impact_env * impact_noise
    impact = thud + snow
    wind_l[impact_start:impact_start + impact_len] += impact
    wind_r[impact_start:impact_start + impact_len] += impact * 0.90

    # Two faint synthetic breath-like exhales at the aftermath; no recorded
    # breathing or clinical sound is implied.
    for onset in (9.45, 10.72):
        first = int(onset * sample_rate)
        length = int(0.72 * sample_rate)
        puff = shaped_noise(length, sample_rate, rng, low=140.0, high=900.0, pink=True)
        t = np.arange(length, dtype=np.float32) / sample_rate
        envelope = np.sin(np.pi * np.clip(t / (length / sample_rate), 0, 1)) ** 1.3
        envelope *= (1.0 - np.exp(-t / 0.08))
        breath = 0.024 * puff * envelope
        wind_l[first:first + length] += breath
        wind_r[first:first + length] += breath * 0.92
        del puff

    left = music_l + wind_l + ski_l
    right = music_r + wind_r + ski_r
    stereo = np.column_stack((left, right))
    peak = float(np.max(np.abs(stereo)))
    if peak > 0.72:
        stereo *= 0.72 / peak
    pcm = np.clip(stereo * 32767.0, -32768, 32767).astype("<i2", copy=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def create_frame(shot_index: int, local_seconds: float, global_seconds: float,
                 images: dict[str, Image.Image], particles, type_layers) -> Image.Image:
    shot = SHOTS[shot_index]
    frame = crop_camera(images[shot.source], shot, local_seconds)
    frame = tint(frame, shot.tone)

    densities = {
        "ski": 145,
        "fall": 230,
        "impact_reveal": 210,
        "aftermath": 52,
        "exterior": 44,
        "arrival": 84,
        "reception": 0,
        "rehab": 0,
        "rehab_detail": 0,
        "team": 0,
        "team_detail": 0,
        "return": 200,
        "sky_rise": 64,
        "endcard": 0,
    }
    density = densities.get(shot.fx, 0)
    strength = 0.35 if shot.fx in ("aftermath", "exterior", "arrival", "sky_rise") else 0.72
    frame = overlay_snow(frame, global_seconds, particles, density, strength)

    if shot.fx == "fall":
        frame = overlay_fall_burst(frame, local_seconds)
        if local_seconds > 1.10:
            alpha = 0.86 * ease((local_seconds - 1.10) / 0.40)
            frame = Image.blend(frame, Image.new("RGB", frame.size, (244, 248, 250)), alpha)
    elif shot.fx == "impact_reveal":
        alpha = 0.86 * (1.0 - ease(local_seconds / 0.42))
        frame = Image.blend(frame, Image.new("RGB", frame.size, (244, 248, 250)), alpha)
    elif shot.fx == "aftermath":
        frame = overlay_breath(frame, local_seconds)

    # A soft warm doorway bloom carries the assisted arrival into reception.
    if shot.fx == "reception" and local_seconds < 0.48:
        bloom_alpha = 0.045 * (1.0 - ease(local_seconds / 0.48))
        bloom = Image.new("RGB", frame.size, (255, 216, 161))
        frame = Image.blend(frame, bloom, bloom_alpha)

    if shot.fx == "endcard":
        frame = add_endcard_type(frame, global_seconds, type_layers)

    # Restrained opening/ending fades. No random camera shake or unmotivated cuts.
    if global_seconds < 0.50:
        frame = Image.blend(Image.new("RGB", frame.size, (3, 8, 13)), frame, ease(global_seconds / 0.50))
    if global_seconds > DURATION - 0.30:
        frame = Image.blend(frame, Image.new("RGB", frame.size, (4, 9, 14)),
                            ease((global_seconds - (DURATION - 0.30)) / 0.30))
    return frame


def render_composite_frame(global_seconds: float, starts: list[float], images,
                           particles, type_layers) -> Image.Image:
    index = len(SHOTS) - 1
    local_seconds = 0.0
    for i, start in enumerate(starts):
        end = start + SHOTS[i].seconds
        if global_seconds < end or i == len(SHOTS) - 1:
            index = i
            local_seconds = max(0.0, min(SHOTS[i].seconds, global_seconds - start))
            break

    current = create_frame(index, local_seconds, global_seconds, images, particles, type_layers)
    transition = SHOTS[index].xfade_in
    if index > 0 and transition > 0 and local_seconds < transition:
        previous = SHOTS[index - 1]
        prev_local = max(0.0, previous.seconds - transition + local_seconds)
        prev_global = starts[index - 1] + prev_local
        outgoing = create_frame(index - 1, prev_local, prev_global, images, particles, type_layers)
        current = Image.blend(outgoing, current, ease(local_seconds / transition))
    return current


def run_checked(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True)


def render(args: argparse.Namespace) -> None:
    sources = verify_sources()
    ffmpeg = get_ffmpeg_exe()
    version = run_checked([ffmpeg, "-hide_banner", "-version"]).stdout.splitlines()[0]
    encoders = run_checked([ffmpeg, "-hide_banner", "-encoders"]).stdout
    if "libx264" not in encoders:
        raise RuntimeError("Selected FFmpeg does not include libx264.")
    serif_path, sans_path = find_font_paths()
    type_layers = make_endcard_layers(serif_path, sans_path)

    images = {key: Image.open(path).convert("RGB") for key, path in sources.items()
              if key not in ("voiceover",)}
    for key, image in images.items():
        if image.size != (1376, 768):
            raise RuntimeError(f"Unexpected dimensions for {key}: {image.size}")
    particles = make_snow()
    frame_counts = [int(round(shot.seconds * FPS)) for shot in SHOTS]
    frame_total = sum(frame_counts)
    if frame_total != int(round(DURATION * FPS)) or abs(sum(s.seconds for s in SHOTS) - DURATION) > 1e-6:
        raise AssertionError(f"Director timeline must total 77 seconds; got {sum(s.seconds for s in SHOTS)}")
    starts: list[float] = []
    cursor = 0.0
    for shot in SHOTS:
        starts.append(cursor)
        cursor += shot.seconds

    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = ROOT / output
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not args.force:
        raise FileExistsError(f"Refusing to overwrite {output}; use --force explicitly.")
    partial = output.with_name(output.stem + ".partial" + output.suffix)
    partial.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory(prefix="altai-directors-cut-") as temp_dir:
        bed_path = Path(temp_dir) / "original_synthetic_score_and_fx.wav"
        write_score_bed(bed_path)
        audio_filter = (
            "[1:a]aresample=48000,asetpts=PTS-STARTPTS,pan=stereo|c0=c0|c1=c0,volume=0.98[voice];"
            "[2:a]aresample=48000,asetpts=PTS-STARTPTS,volume=1.0[bed];"
            "[voice]asplit=2[voice_mix][voice_key];"
            # Pad only the side-chain detector, not the approved narration, so
            # the original voice ends naturally while the score resolves to 77 s.
            "[voice_key]apad=pad_dur=7,atrim=duration=77[voice_key_padded];"
            "[bed][voice_key_padded]sidechaincompress=threshold=0.048:ratio=1.8:"
            "attack=55:release=520:makeup=1[ducked];"
            "[voice_mix][ducked]amix=inputs=2:duration=longest:normalize=0,"
            "alimiter=limit=0.91:attack=5:release=60[aout]"
        )
        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}",
            "-framerate", str(FPS), "-i", "pipe:0", "-i", str(VOICEOVER), "-i", str(bed_path),
            "-filter_complex", audio_filter, "-map", "0:v:0", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-profile:v", "high",
            "-level:v", "4.1", "-pix_fmt", "yuv420p", "-r", str(FPS), "-fps_mode", "cfr",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-t", f"{DURATION:.3f}", "-movflags", "+faststart",
            "-metadata", "title=Altai Rehabilitation Center — Director's Cut v2",
            "-metadata", "comment=AI-generated still keyframes and programmatic 2D motion; no generated video footage",
            str(partial),
        ]
        print(f"Renderer: {version}")
        print(f"Typography: supersampled DejaVu Serif/Sans; no logo/emblem used")
        print(f"Sources verified: {len(SOURCE_HASHES)} files; timeline {DURATION:.1f} s / {frame_total} frames")
        print("Motion provenance: still-image camera paths, snow/breath/impact layers, and AI-generated still inserts")
        start_time = time.monotonic()
        with tempfile.TemporaryFile(mode="w+t") as log:
            process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE,
                                       stdout=subprocess.DEVNULL, stderr=log, bufsize=0)
            assert process.stdin is not None
            written = 0
            try:
                for index in range(frame_total):
                    seconds = index / FPS
                    frame = render_composite_frame(seconds, starts, images, particles, type_layers)
                    process.stdin.write(frame.tobytes())
                    written += 1
                    if written % (FPS * 8) == 0:
                        elapsed = time.monotonic() - start_time
                        print(f"  {written:4d}/{frame_total} frames ({seconds:5.1f}s) — {elapsed:.0f}s elapsed", flush=True)
                process.stdin.close()
                code = process.wait()
            except BrokenPipeError:
                process.stdin.close()
                code = process.wait()
            if code:
                log.seek(0)
                raise RuntimeError(f"FFmpeg render failed (exit {code}):\n{log.read()}")

        if not partial.is_file() or partial.stat().st_size < 500_000:
            raise RuntimeError("Render completed without a plausible MP4 file.")
        check = subprocess.run([ffmpeg, "-hide_banner", "-v", "error", "-i", str(partial),
                                "-f", "null", "-"], cwd=ROOT, capture_output=True, text=True)
        if check.returncode:
            partial.unlink(missing_ok=True)
            raise RuntimeError(f"Rendered MP4 failed full decode verification:\n{check.stderr}")

    # Confirm source files are still byte-identical before publishing.
    verify_sources()
    if output.exists() and args.force:
        output.unlink()
    partial.replace(output)
    print(f"Playable MP4 verified: {output}")
    print(f"Size: {output.stat().st_size:,} bytes")
    print(f"SHA-256: {sha256(output)}")
    print(f"Elapsed: {time.monotonic() - start_time:.1f} s")
    probe = subprocess.run([ffmpeg, "-hide_banner", "-i", str(output), "-map", "0:v:0",
                            "-frames:v", "1", "-f", "null", "-"],
                           cwd=ROOT, capture_output=True, text=True)
    print(probe.stderr)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        verify_sources()
        if args.verify_only:
            ffmpeg = get_ffmpeg_exe()
            version = run_checked([ffmpeg, "-hide_banner", "-version"]).stdout.splitlines()[0]
            serif, sans = find_font_paths()
            print(f"Hash-pinned sources verified: {len(SOURCE_HASHES)}")
            print(f"FFmpeg: {version}")
            print(f"Fonts: {serif.name}, {sans.name}")
            print(f"Timeline: {sum(s.seconds for s in SHOTS):.1f}s / {sum(int(round(s.seconds * FPS)) for s in SHOTS)} frames")
            print("I2V capability: not present; this workflow is still-based/programmatic")
            return 0
        render(args)
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
