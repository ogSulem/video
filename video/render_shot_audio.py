#!/usr/bin/env python3
"""Deterministic sound design for the 5-second carve-and-fall shot.

Everything is synthesised from filtered noise and simple modal resonances --
no third-party recordings, samples or music. The bed follows the same timeline
as the picture:

  0.0-1.3 s  a clean carved arc: steady edge hiss + soft wind
  1.35 s      the edge lets go: hiss turns gritty, brief low-frequency slip
  2.8 s       the washout: spray swelling, wind rising
  3.7 s       impact with the powder: a soft muffled "poomf" and spray burst
  4.1-5.0 s   the snow settles; wind remains, everything else falls away

Output: 48 kHz, 16-bit stereo WAV.
"""

from __future__ import annotations

import argparse
import wave
from pathlib import Path

import numpy as np

SR = 48000
DURATION = 5.0

HERE = Path(__file__).resolve().parent
OUT = HERE / "shots" / "altai_carve_fall_v1" / "out" / "altai_carve_fall_v1_audio.wav"


def _noise(n, seed):
    rng = np.random.default_rng(seed)
    return rng.normal(0, 1, n).astype(np.float64)


def _bandpass(x, lo, hi, seed=0):
    """Cheap, stable band-limited noise via FFT masking."""
    n = len(x)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1.0 / SR)
    mask = np.ones_like(freqs)
    if lo > 0:
        mask *= 1.0 / (1.0 + (lo / np.maximum(freqs, 1e-6)) ** 4)
    if hi < SR / 2:
        mask *= 1.0 / (1.0 + (freqs / hi) ** 4)
    return np.fft.irfft(spec * mask, n)


def _env(n, points):
    """Piecewise-linear envelope from (time, value) pairs, smoothed."""
    t = np.arange(n) / SR
    xs = np.array([p[0] for p in points], dtype=float)
    ys = np.array([p[1] for p in points], dtype=float)
    e = np.interp(t, xs, ys)
    # short exponential smoothing removes corner artefacts
    k = 0.02
    out = np.empty_like(e)
    acc = e[0]
    for i in range(len(e)):
        acc += (e[i] - acc) * k
        out[i] = acc
    return out


def build():
    n = int(round(SR * DURATION))
    t = np.arange(n) / SR

    # --- wind bed: two decorrelated bands, gently animated ---
    wind_a = _bandpass(_noise(n, 1), 90, 900)
    wind_b = _bandpass(_noise(n, 2), 300, 2600)
    wind_env = _env(n, [(0.0, 0.20), (1.3, 0.22), (2.7, 0.34), (3.7, 0.40),
                        (4.2, 0.26), (5.0, 0.18)])
    wind = (wind_a * 0.55 + wind_b * 0.45) * wind_env

    # --- edge hiss: the ski carving, then slipping, then gone ---
    hiss = _bandpass(_noise(n, 3), 1400, 8000)
    hiss_env = _env(n, [(0.0, 0.30), (0.9, 0.34), (1.35, 0.36), (1.6, 0.22),
                        (2.2, 0.26), (2.85, 0.30), (3.3, 0.16), (3.75, 0.05),
                        (4.0, 0.04), (4.4, 0.0), (5.0, 0.0)])
    hiss *= hiss_env

    # grit: broadband crackle while the edge is failing
    grit = _bandpass(_noise(n, 4), 600, 5000)
    grit_env = _env(n, [(1.30, 0.0), (1.45, 0.20), (2.1, 0.14), (2.85, 0.22),
                        (3.4, 0.10), (3.8, 0.0), (5.0, 0.0)])
    grit *= grit_env * (1.0 + 0.6 * np.sin(2 * np.pi * 7.3 * t) ** 2)

    # --- impact: a soft, low powder thump plus a short spray ---
    impact = np.zeros(n)
    t0 = 3.70
    idx = int(t0 * SR)
    ln = int(0.55 * SR)
    tt = np.arange(ln) / SR
    body = (np.sin(2 * np.pi * 62 * tt) * 0.55
            + np.sin(2 * np.pi * 96 * tt + 0.7) * 0.30
            + np.sin(2 * np.pi * 141 * tt + 1.9) * 0.15)
    body *= np.exp(-tt / 0.115)
    spray = _bandpass(_noise(ln, 5), 700, 6500) * np.exp(-tt / 0.20) * 0.55
    impact[idx:idx + ln] += body * 0.8 + spray

    # rebound puff a beat later
    idx2 = int(3.96 * SR)
    ln2 = int(0.35 * SR)
    tt2 = np.arange(ln2) / SR
    puff = _bandpass(_noise(ln2, 6), 900, 7000) * np.exp(-tt2 / 0.11) * 0.22
    impact[idx2:idx2 + ln2] += puff[:max(0, min(ln2, n - idx2))]

    # --- tiny ski chatter before the slip, for texture ---
    chat = _bandpass(_noise(n, 7), 1800, 4400)
    chat_env = _env(n, [(0.0, 0.0), (0.35, 0.06), (0.9, 0.045), (1.3, 0.02), (1.6, 0.0),
                        (5.0, 0.0)])
    chat *= chat_env

    mono = wind * 0.9 + hiss * 0.55 + grit * 0.5 + impact * 1.0 + chat * 0.8

    # gentle low-shelf removal and peak limiting
    mono = np.tanh(mono * 1.15) * 0.85
    peak = np.max(np.abs(mono)) or 1.0
    mono = mono / peak * 0.72

    # faux stereo: tiny decorrelated delay and level offset per side
    delay = int(0.0042 * SR)
    left = mono.copy()
    right = np.concatenate([np.zeros(delay), mono[:-delay]]) * 0.97
    right += _bandpass(_noise(n, 9), 200, 6000) * 0.012
    stereo = np.stack([left, right], axis=1)

    # fade the last 250 ms so the shot ends cleanly
    fade = int(0.25 * SR)
    stereo[-fade:] *= np.linspace(1.0, 0.0, fade)[:, None]
    return stereo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists() and not args.force:
        print(f"refusing to overwrite {OUT} (pass --force)")
        return 2

    stereo = build()
    pcm = np.clip(stereo, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    with wave.open(str(OUT), "wb") as fh:
        fh.setnchannels(2)
        fh.setsampwidth(2)
        fh.setframerate(SR)
        fh.writeframes(pcm.tobytes())
    print(f"wrote {OUT}  ({pcm.shape[0] / SR:.2f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
