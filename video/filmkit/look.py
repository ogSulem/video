"""The look: one grade for the whole film, applied to every frame.

The three generated clips arrive with three different cameras and three
different colour temperatures; the approved stills arrive with a fourth. A film
needs one look, so every frame -- footage or living still, interior or slope --
goes through the same finishing chain here:

    white balance -> lift/gamma/gain -> filmic contrast -> saturation
    -> halation/bloom -> vignette -> grain -> delivery encode

Per-segment ``Grade`` values move the temperature and contrast so the story
still travels from cold morning to warm golden hour; the chain itself never
changes, which is what makes the cut feel like one camera.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

cv2.setNumThreads(max(1, min(4, cv2.getNumberOfCPUs())))


@dataclass(frozen=True)
class Grade:
    """Per-segment colour parameters. All defaults are neutral."""

    temperature: float = 0.0   # -1 cold/blue .. +1 warm/amber
    tint: float = 0.0          # -1 green .. +1 magenta
    exposure: float = 0.0      # stops
    contrast: float = 0.10     # filmic S-curve strength
    saturation: float = 1.0
    lift: float = 0.0          # raises shadows (film base)
    gamma: float = 1.0
    gain: float = 1.0
    bloom: float = 0.10
    halation: float = 0.05
    grain: float = 1.5
    vignette: float = 0.16
    sharpen: float = 0.15
    shadow_tint: tuple[float, float, float] = (0.0, 0.0, 0.0)
    highlight_tint: tuple[float, float, float] = (0.0, 0.0, 0.0)


def _channel_luts(grade: Grade) -> np.ndarray:
    """A 3 x 256 uint8 LUT holding balance, levels and the contrast curve."""
    x = np.arange(256, dtype=np.float32) / 255.0
    # exposure
    x = x * (2.0 ** grade.exposure)
    # white balance in linear-ish space; small, believable offsets
    warm = np.array([1.0 + 0.085 * grade.temperature, 1.0 + 0.012 * grade.temperature,
                     1.0 - 0.095 * grade.temperature], dtype=np.float32)
    magenta = np.array([1.0 + 0.03 * grade.tint, 1.0 - 0.055 * grade.tint,
                        1.0 + 0.03 * grade.tint], dtype=np.float32)
    chans = []
    for c in range(3):
        v = np.clip(x * warm[c] * magenta[c], 0.0, 4.0)
        v = v * grade.gain + grade.lift * (1.0 - v)
        v = np.clip(v, 0.0, 1.0) ** (1.0 / max(grade.gamma, 1e-3))
        # filmic contrast: a soft S that never clips the snow highlights
        s = grade.contrast
        v = np.clip(v + s * (v - 0.5) * (1.0 - np.abs(v - 0.5) * 1.35) * 2.0, 0.0, 1.0)
        # split tone: cool the shadows, warm the highlights -- the single most
        # effective "this was graded" cue, and it costs nothing here because it
        # rides along inside the same per-channel curve
        v = v + grade.shadow_tint[c] * (1.0 - v) ** 1.6 + grade.highlight_tint[c] * v ** 1.8
        chans.append(np.clip(v, 0.0, 1.0))
    lut = np.stack(chans, axis=1)  # (256, 3)
    return (np.clip(lut, 0, 1) * 255.0 + 0.5).astype(np.uint8)


class Look:
    """Compiled finishing chain for one segment."""

    def __init__(self, grade: Grade):
        self.grade = grade
        self._lut = _channel_luts(grade)
        self._lut3 = self._lut.reshape(1, 256, 3)

    def __call__(self, rgb: np.ndarray, t: float, seed: int = 0) -> np.ndarray:
        g = self.grade
        img = cv2.LUT(rgb, self._lut3)

        if abs(g.saturation - 1.0) > 1e-3:
            # one 3x3 luma-preserving matrix in uint8: same result as the float
            # blend, a fraction of the cost
            s_ = g.saturation
            lr, lg, lb = 0.2126, 0.7152, 0.0722
            matrix = np.array([
                [lr + (1 - lr) * s_, lg - lg * s_, lb - lb * s_],
                [lr - lr * s_, lg + (1 - lg) * s_, lb - lb * s_],
                [lr - lr * s_, lg - lg * s_, lb + (1 - lb) * s_],
            ], np.float32)
            img = cv2.transform(img, matrix)

        if g.bloom > 0.0 or g.halation > 0.0:
            img = _glow(img, g.bloom, g.halation)

        if g.vignette > 0.0:
            img = _vignette(img, g.vignette)

        if g.grain > 0.0:
            img = _grain(img, g.grain, seed, t)

        if g.sharpen > 0.0:
            # everything in this film is either upscaled footage or an
            # upscaled plate; a small unsharp at the very end restores the
            # micro-contrast the scaler took away, before the grain sits on top
            blur = cv2.GaussianBlur(img, (0, 0), 1.15)
            img = cv2.addWeighted(img, 1.0 + g.sharpen, blur, -g.sharpen, 0.0)
        return img


def _glow(img: np.ndarray, bloom: float, halation: float) -> np.ndarray:
    """Highlight bloom plus a warm halation ring, both from one blurred pass.

    Everything is done at quarter resolution and added once at full size: the
    effect is a wide soft glow, so calculating it at 480x270 costs nothing in
    the picture and saves most of the per-frame budget.
    """
    h, w = img.shape[:2]
    small = cv2.resize(img, (max(2, w // 4), max(2, h // 4)), interpolation=cv2.INTER_AREA)
    f = small.astype(np.float32)
    luma = (f[..., 0] * 0.2126 + f[..., 1] * 0.7152 + f[..., 2] * 0.0722) / 255.0
    hi = np.clip((luma - 0.70) / 0.30, 0.0, 1.0)[..., None]
    bright = f * hi
    glow = cv2.GaussianBlur(bright, (0, 0), 8.0)
    halo = cv2.GaussianBlur(bright * np.array([1.0, 0.70, 0.42], np.float32), (0, 0), 16.0)
    add = (glow * (0.85 * bloom) + halo * (1.05 * halation)).astype(np.float32)
    if add.max() <= 0.0:
        return img
    add = cv2.resize(add, (w, h), interpolation=cv2.INTER_LINEAR)
    base = img.astype(np.float32)
    # screen blend: highlights roll off instead of clipping flat
    out = 255.0 - (255.0 - base) * (255.0 - add) / 255.0
    return np.clip(out, 0, 255).astype(np.uint8)


_VIG_CACHE: dict[tuple[int, int, float], np.ndarray] = {}


def _vignette(img: np.ndarray, strength: float) -> np.ndarray:
    h, w = img.shape[:2]
    key = (h, w, round(strength, 3))
    mask = _VIG_CACHE.get(key)
    if mask is None:
        ys = np.linspace(-1.0, 1.0, h, dtype=np.float32)[:, None]
        xs = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
        r = np.sqrt(xs * xs * 0.90 + ys * ys * 0.98)
        mask = np.clip(1.0 - strength * np.clip(r - 0.52, 0.0, 2.0) ** 1.7, 0.0, 1.0)
        mask = mask.astype(np.float32)[..., None]
        _VIG_CACHE[key] = mask
    return np.clip(img.astype(np.float32) * mask, 0, 255).astype(np.uint8)


def _grain(img: np.ndarray, amount: float, seed: int, t: float) -> np.ndarray:
    """Fine, luminance-weighted grain: strongest in the mids, gone in snow."""
    h, w = img.shape[:2]
    qw, qh = max(2, w // 3), max(2, h // 3)
    rng = np.random.default_rng((seed * 7919) ^ int(t * 1000))
    noise = rng.normal(0.0, 1.0, (qh, qw)).astype(np.float32)
    noise = cv2.GaussianBlur(noise, (0, 0), 0.55)
    noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_LINEAR)
    f = img.astype(np.float32)
    luma = (f[..., 0] * 0.2126 + f[..., 1] * 0.7152 + f[..., 2] * 0.0722) * (1.0 / 255.0)
    weight = np.clip(1.0 - np.abs(luma - 0.50) * 1.7, 0.18, 1.0) * (amount / 255.0)
    # slightly chromatic grain reads warmer than pure luma noise
    f += (noise * weight)[..., None] * np.array([255.0, 242.0, 224.0], np.float32)
    return np.clip(f, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------
# transitions
# --------------------------------------------------------------------------
def dissolve(a: np.ndarray, b: np.ndarray, p: float) -> np.ndarray:
    p = float(np.clip(p, 0.0, 1.0))
    if p <= 0.0:
        return a
    if p >= 1.0:
        return b
    f = a.astype(np.float32) * (1.0 - p) + b.astype(np.float32) * p
    return np.clip(f, 0, 255).astype(np.uint8)


def dip(img: np.ndarray, colour: tuple[float, float, float], amount: float) -> np.ndarray:
    """Dip toward a flat colour: 1.0 is fully that colour."""
    amount = float(np.clip(amount, 0.0, 1.0))
    if amount <= 0.0:
        return img
    f = img.astype(np.float32) * (1.0 - amount) + np.array(colour, np.float32) * 255.0 * amount
    return np.clip(f, 0, 255).astype(np.uint8)


WHITE = (0.985, 0.985, 1.0)
BLACK = (0.0, 0.0, 0.0)
