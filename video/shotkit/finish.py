"""Film finishing pass: gentle lens softness, tone curve, grain, vignette."""

from __future__ import annotations

import cv2
import numpy as np


def _tone_curve(img: np.ndarray) -> np.ndarray:
    """Very light S-curve plus a cool-shadow/warm-highlight split-tone."""
    x = np.clip(img / 255.0, 0.0, 1.0)
    # filmic contrast: keeps highlights from clipping in the snow
    y = x + 0.055 * (np.sin((x - 0.5) * np.pi) * -1.0 + 0.0) * 0.0
    y = np.where(x < 0.5, x * (1.0 + 0.06 * (0.5 - x)), x)
    y = np.where(x > 0.5, 1.0 - (1.0 - x) * (1.0 + 0.05 * (x - 0.5)), y)
    y = np.clip(y, 0.0, 1.0)

    luma = y.mean(axis=2, keepdims=True)
    split = np.array([0.012, 0.006, -0.010], dtype=np.float32)  # cool shadows
    warm = np.array([0.014, 0.008, -0.008], dtype=np.float32)   # warm highlights
    y = y + split * (1.0 - luma) + warm * luma
    return np.clip(y * 255.0, 0.0, 255.0)


def _vignette(h: int, w: int, strength: float = 0.16) -> np.ndarray:
    ys = np.linspace(-1.0, 1.0, h, dtype=np.float32)[:, None]
    xs = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    r = np.sqrt(xs * xs * 0.92 + ys * ys)
    v = 1.0 - strength * np.clip(r - 0.55, 0.0, 1.0) ** 1.6 * 2.0
    return np.clip(v, 0.0, 1.0)[..., None]


def finish_frame(img: np.ndarray, t: float, seed: int = 0, grain: float = 1.2,
                 softness: float = 0.55) -> np.ndarray:
    out = _tone_curve(img.astype(np.float32))

    # very slight lens softness, strongest at the frame edges
    blurred = cv2.GaussianBlur(out, (0, 0), 0.9)
    h, w = out.shape[:2]
    ys = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    xs = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    r = np.clip(np.sqrt(xs * xs + ys * ys) / 1.4, 0.0, 1.0)[..., None]
    mix = (r ** 2) * softness
    out = out * (1.0 - mix) + blurred * mix

    out *= _vignette(h, w)

    rng = np.random.default_rng(1000 + seed)
    noise = rng.normal(0.0, 1.0, (h, w, 1)).astype(np.float32)
    noise = cv2.GaussianBlur(noise, (0, 0), 0.55).reshape(h, w, 1) * grain
    # grain is most visible in the mids (as with film); fade it in the snow highlights
    luma = out.mean(axis=2, keepdims=True) / 255.0
    weight = np.clip(1.0 - np.abs(luma - 0.55) * 1.5, 0.25, 1.0)
    weight = weight.repeat(3, axis=2)
    out = out + noise * weight

    return np.clip(out, 0.0, 255.0)
