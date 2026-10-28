"""Original score, sound design and final mix.

Everything here is synthesised locally: no third-party music, no sample
libraries, no external service. Three parts are built and then mixed:

* the **locked Russian voice-over**, decoded untouched from the approved MP3
  and never re-timed, re-worded or edited;
* an **original score** — warm detuned pads, a felt-piano figure, a restrained
  sub pulse — through a synthesised stereo reverb;
* **sound design** — alpine wind, ski edge on cold snow, one soft snow impact,
  air whooshes on the big transitions.

The mix is then normalised to a delivery loudness target (-16 LUFS integrated,
-1.5 dBTP) in two passes through FFmpeg's EBU R128 meter.
"""

from __future__ import annotations

import json
import math
import subprocess
import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SR = 48000

# Music bed tone: (Hz, dB). The sub stays, but it must not dominate a mix whose
# only job in the midrange is to sit under a spoken voice.
MUSIC_EQ = ((25.0, -9.0), (45.0, -5.0), (90.0, -2.0), (200.0, 0.0),
            (900.0, 0.8), (2600.0, 1.4), (6000.0, 0.0), (14000.0, -2.0))


# --------------------------------------------------------------------------
# i/o helpers
# --------------------------------------------------------------------------
def ffmpeg_exe() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def decode_voiceover(path: Path, sr: int = SR) -> np.ndarray:
    """Decode the approved VO to float32 stereo (n, 2) at ``sr``."""
    cmd = [ffmpeg_exe(), "-v", "error", "-i", str(path), "-ac", "2", "-ar", str(sr),
           "-f", "f32le", "-"]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"cannot decode voice-over: {proc.stderr.decode()[:400]}")
    data = np.frombuffer(proc.stdout, dtype="<f4").astype(np.float32)
    return data.reshape(-1, 2).copy()


def write_wav(path: Path | str, stereo: np.ndarray, sr: int = SR) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(stereo, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sr)
        handle.writeframes(pcm.tobytes())


def _envelope(n: int, keys: list[tuple[float, float]], sr: int) -> np.ndarray:
    t = np.arange(n, dtype=np.float32) / sr
    xs = np.array([k[0] for k in keys], np.float32)
    ys = np.array([k[1] for k in keys], np.float32)
    return np.interp(t, xs, ys).astype(np.float32)


# --------------------------------------------------------------------------
# instruments
# --------------------------------------------------------------------------
def midi_hz(note: float) -> float:
    return 440.0 * 2.0 ** ((note - 69.0) / 12.0)


def _pad_note(t: np.ndarray, freq: float, rng, detune_cents: float = 6.0) -> tuple[np.ndarray, np.ndarray]:
    """One stereo pad voice: three detuned partial groups with a soft top."""
    left = np.zeros_like(t)
    right = np.zeros_like(t)
    for cents, pan in ((0.0, 0.0), (detune_cents, 0.55), (-detune_cents, -0.55)):
        f = freq * 2.0 ** (cents / 1200.0)
        phase = float(rng.uniform(0, 2 * np.pi))
        # a sawtooth built from harmonics with a gentle natural roll-off
        voice = np.zeros_like(t)
        for h, amp in ((1, 1.0), (2, 0.34), (3, 0.17), (4, 0.09), (5, 0.045), (6, 0.022)):
            if f * h > 9000:
                continue
            voice += amp * np.sin(2 * np.pi * f * h * t + phase * h * 0.7)
        voice /= 1.55
        # slow amplitude shimmer, different per voice
        lfo = 1.0 + 0.10 * np.sin(2 * np.pi * (0.07 + 0.03 * abs(pan)) * t + phase)
        voice = voice * lfo
        left += voice * (1.0 - max(pan, 0.0)) * 0.5
        right += voice * (1.0 + min(pan, 0.0)) * 0.5
    return left, right


def _felt_piano(freq: float, dur: float, sr: int, rng, velocity: float = 1.0) -> np.ndarray:
    n = int(dur * sr)
    t = np.arange(n, dtype=np.float32) / sr
    f = freq
    # slight inharmonicity and a fast attack, felted (soft) timbre
    tone = (0.62 * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))
            + 0.24 * np.sin(2 * np.pi * f * 2.002 * t + rng.uniform(0, 6.28))
            + 0.11 * np.sin(2 * np.pi * f * 3.008 * t + rng.uniform(0, 6.28))
            + 0.05 * np.sin(2 * np.pi * f * 4.02 * t + rng.uniform(0, 6.28)))
    env = (1.0 - np.exp(-t / 0.006)) * np.exp(-t / (0.9 + 0.5 / max(f / 220.0, 0.3)))
    # a touch of hammer noise
    noise = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.004) * 0.05
    return (tone * env + noise) * velocity


def _reverb_ir(seconds: float, sr: int, rng, bright: float = 0.55) -> np.ndarray:
    """Synthetic stereo impulse: dense early field, exponentially darkening tail."""
    n = int(seconds * sr)
    t = np.arange(n, dtype=np.float32) / sr
    decay = np.exp(-t / (seconds * 0.33))
    ir = rng.standard_normal((n, 2)).astype(np.float32) * decay[:, None]
    # darken over time with a moving average whose window grows
    kernel = np.hanning(64).astype(np.float32)
    kernel /= kernel.sum()
    smooth = np.apply_along_axis(lambda m: np.convolve(m, kernel, mode="same"), 0, ir)
    mix = np.clip(t / (seconds * 0.45), 0.0, 1.0)[:, None]
    ir = ir * (1.0 - mix * bright) + smooth * (mix * bright)
    # early reflections
    for delay_ms, gain in ((11, 0.5), (19, 0.38), (27, 0.3), (41, 0.22), (59, 0.16)):
        i = int(delay_ms / 1000.0 * sr)
        if i < n:
            ir[i:i + 40] += (rng.standard_normal((min(40, n - i), 2)).astype(np.float32)
                             * gain * np.linspace(1.0, 0.0, min(40, n - i))[:, None])
    ir /= np.abs(ir).max()
    return ir


def convolve_stereo(signal: np.ndarray, ir: np.ndarray) -> np.ndarray:
    """FFT overlap-add convolution, block by block (numpy only)."""
    n = signal.shape[0]
    m = ir.shape[0]
    block = 65536
    nfft = 1
    while nfft < block + m - 1:
        nfft *= 2
    out = np.zeros((n + m - 1, 2), np.float32)
    ir_f = np.fft.rfft(ir, n=nfft, axis=0)
    for start in range(0, n, block):
        chunk = signal[start:start + block]
        if chunk.shape[0] < block:
            chunk = np.pad(chunk, ((0, block - chunk.shape[0]), (0, 0)))
        spec = np.fft.rfft(chunk, n=nfft, axis=0) * ir_f
        y = np.fft.irfft(spec, n=nfft, axis=0)[:block + m - 1]
        take = min(y.shape[0], out.shape[0] - start)
        if take <= 0:
            break
        out[start:start + take] += y[:take].astype(np.float32)
    return out[:n]


# --------------------------------------------------------------------------
# score plan
# --------------------------------------------------------------------------
@dataclass
class MusicPlan:
    """Musical shape of the film. Times in seconds."""

    duration: float
    chords: list[tuple[float, float, list[int], str]] = field(default_factory=list)
    piano: list[tuple[float, float]] = field(default_factory=list)          # (time, midi)
    pulses: list[tuple[float, float]] = field(default_factory=list)         # (time, strength)
    gain_keys: list[tuple[float, float]] = field(default_factory=list)
    wind_keys: list[tuple[float, float]] = field(default_factory=list)
    ski_keys: list[tuple[float, float]] = field(default_factory=list)
    impact: float | None = None
    whooshes: list[tuple[float, float]] = field(default_factory=list)       # (time, strength)
    breath: list[float] = field(default_factory=list)
    reverb_wet: float = 0.42


def render_score(plan: MusicPlan, sr: int = SR, seed: int = 5) -> np.ndarray:
    """Render the full score + design to stereo float32, dry and wet summed."""
    n = int(plan.duration * sr) + sr // 2
    t_all = np.arange(n, dtype=np.float32) / sr
    rng = np.random.default_rng(seed)

    pad_l = np.zeros(n, np.float32)
    pad_r = np.zeros(n, np.float32)
    piano_l = np.zeros(n, np.float32)
    piano_r = np.zeros(n, np.float32)
    sub = np.zeros(n, np.float32)

    for i, (start, end, notes, voice) in enumerate(plan.chords):
        first = max(0, int(start * sr))
        last = min(n, int((end + 1.6) * sr))
        if last <= first:
            continue
        seg_t = np.arange(first, last, dtype=np.float32) / sr - start
        # slow swell in, longer release out
        attack = np.clip(seg_t / 1.9, 0.0, 1.0) ** 1.6
        release = np.clip(((end + 1.6) - start - seg_t) / 2.4, 0.0, 1.0) ** 1.3
        env = (attack * release).astype(np.float32)
        level = 0.055 if voice == "warm" else (0.040 if voice == "air" else 0.075)
        for j, note in enumerate(notes):
            l, r = _pad_note(seg_t, midi_hz(note), rng, detune_cents=5.0 + 1.5 * (j % 3))
            pad_l[first:last] += l * env * level
            pad_r[first:last] += r * env * level
            # a quiet octave-up shimmer keeps the top from sounding dull
            if j == len(notes) - 1:
                l2, r2 = _pad_note(seg_t, midi_hz(note + 12), rng, detune_cents=8.0)
                pad_l[first:last] += l2 * env * level * 0.22
                pad_r[first:last] += r2 * env * level * 0.22
        # sub root, an octave below the lowest pad note
        root = midi_hz(notes[0] - 12)
        tt = np.arange(first, last, dtype=np.float32) / sr
        sub_env = (attack * release).astype(np.float32)
        sub[first:last] += (0.018 * np.sin(2 * np.pi * root * tt) * sub_env).astype(np.float32)

    for when, note in plan.piano:
        start = int(when * sr)
        if start >= n:
            continue
        tone = _felt_piano(midi_hz(note), min(3.4, plan.duration - when + 0.4), sr, rng)
        end = min(n, start + tone.shape[0])
        pan = 0.5 + 0.22 * math.sin(note * 0.7)
        piano_l[start:end] += tone[: end - start] * (1.0 - pan) * 0.30
        piano_r[start:end] += tone[: end - start] * pan * 0.30

    for when, strength in plan.pulses:
        start = int(when * sr)
        if start >= n:
            continue
        length = int(0.42 * sr)
        tt = np.arange(length, dtype=np.float32) / sr
        env = (1.0 - np.exp(-tt / 0.008)) * np.exp(-tt / 0.16)
        thump = np.sin(2 * np.pi * 52.0 * tt) * env * 0.075 * strength
        end = min(n, start + length)
        pad_l[start:end] += thump[: end - start]
        pad_r[start:end] += thump[: end - start] * 0.94

    music_gain = _envelope(n, plan.gain_keys, sr)
    pad_l *= music_gain
    pad_r *= music_gain
    piano_l *= music_gain
    piano_r *= music_gain
    sub *= music_gain

    # ---- reverb -----------------------------------------------------------
    ir = _reverb_ir(2.6, sr, rng)
    dry = np.stack([pad_l + piano_l, pad_r + piano_r], axis=1)
    wet = convolve_stereo(dry, ir) * plan.reverb_wet
    score = dry + wet
    score += np.stack([sub, sub], axis=1)

    # Tone: roll the very bottom off the bed so it supports the narration
    # instead of crowding it, and lift presence slightly. Applied to the music
    # only -- the voice-over gets no EQ at all.
    score = eq_curve(score, sr, MUSIC_EQ)

    # ---- design -----------------------------------------------------------
    sfx = np.zeros((n, 2), np.float32)

    if plan.wind_keys:
        wind = rng.standard_normal(n).astype(np.float32)
        # cheap band shaping: two moving averages as a broad band-pass, then
        # periodic gusts so it breathes instead of hissing
        k = int(sr / 220)
        low = np.convolve(wind, np.ones(k, np.float32) / k, mode="same")
        k2 = int(sr / 900)
        low = np.convolve(low, np.ones(k2, np.float32) / k2, mode="same")
        band = wind - low
        band /= max(float(np.abs(band).max()), 1e-6)
        gust = 0.55 + 0.45 * np.sin(2 * np.pi * 0.085 * t_all + 0.7) * np.sin(2 * np.pi * 0.031 * t_all)
        g = _envelope(n, plan.wind_keys, sr) * gust
        s = 0.055 * band * g
        sfx[:, 0] += s * 0.95
        sfx[:, 1] += np.roll(s, 311) * 0.85

    if plan.ski_keys:
        hiss = rng.standard_normal(n).astype(np.float32)
        k = int(sr / 2600)
        hiss = np.convolve(hiss, np.ones(k, np.float32) / k, mode="same")
        hiss -= np.convolve(hiss, np.ones(int(sr / 90), np.float32) / int(sr / 90), mode="same")
        hiss /= max(float(np.abs(hiss).max()), 1e-6)
        carve = _envelope(n, plan.ski_keys, sr) * (0.65 + 0.35 * np.sin(2 * np.pi * 1.7 * t_all))
        s = 0.030 * hiss * carve
        sfx[:, 0] += s * 0.9
        sfx[:, 1] += np.roll(s, 173) * 0.9

    if plan.impact is not None:
        start = int(plan.impact * sr)
        length = int(0.9 * sr)
        end = min(n, start + length)
        tt = np.arange(end - start, dtype=np.float32) / sr
        env = (1.0 - np.exp(-tt / 0.004)) * np.exp(-tt / 0.19)
        body = np.sin(2 * np.pi * 61.0 * tt) * env * 0.16
        crunch = rng.standard_normal(end - start).astype(np.float32) * env * 0.05
        k = int(sr / 1400)
        crunch = np.convolve(crunch, np.ones(k, np.float32) / k, mode="same")
        hit = body + crunch
        sfx[start:end, 0] += hit
        sfx[start:end, 1] += hit * 0.92

    for when, strength in plan.whooshes:
        start = int(when * sr)
        length = int(1.1 * sr)
        end = min(n, start + length)
        if end <= start:
            continue
        tt = np.arange(end - start, dtype=np.float32) / sr
        env = np.sin(np.pi * np.clip(tt / (length / sr), 0, 1)) ** 2.0
        noise = rng.standard_normal(end - start).astype(np.float32)
        k = int(sr / 700)
        noise = np.convolve(noise, np.ones(k, np.float32) / k, mode="same")
        noise /= max(float(np.abs(noise).max()), 1e-6)
        sweep = np.stack([noise * env * 0.035 * strength,
                          np.roll(noise, 200) * env * 0.033 * strength], axis=1)
        sfx[start:end] += sweep

    for when in plan.breath:
        start = int(when * sr)
        length = int(0.75 * sr)
        end = min(n, start + length)
        if end <= start:
            continue
        tt = np.arange(end - start, dtype=np.float32) / sr
        env = np.sin(np.pi * np.clip(tt / (length / sr), 0, 1)) ** 1.4
        noise = rng.standard_normal(end - start).astype(np.float32)
        k = int(sr / 600)
        noise = np.convolve(noise, np.ones(k, np.float32) / k, mode="same")
        noise /= max(float(np.abs(noise).max()), 1e-6)
        puff = noise * env * 0.018
        sfx[start:end, 0] += puff
        sfx[start:end, 1] += puff * 0.9

    return (score[: n] + sfx)[: int(plan.duration * sr)]


# --------------------------------------------------------------------------
# mix
# --------------------------------------------------------------------------
def declick(x: np.ndarray, sr: int = SR, threshold: float = 0.34,
            merge: int = 6) -> tuple[np.ndarray, list[tuple[float, int]]]:
    """Repair isolated impulse artefacts (MP3 frame-boundary cracks).

    A codec crack is a short burst of samples whose slope is far above anything
    the waveform around it produces; speech transients are spread over many
    samples and never look like that. Bad samples closer than ``merge`` are
    treated as one burst, and the burst plus a few samples either side is
    rebuilt by linear interpolation between the clean edges.

    This works on the in-memory placement copy only. The approved file stays
    byte-identical, and neither timing, wording nor performance is changed.
    Returns the repaired copy and (seconds, samples) per repair.
    """
    mono = x.max(axis=1)
    delta = np.abs(np.diff(mono))
    bad = np.flatnonzero(delta > threshold)
    if bad.size == 0:
        return x, []
    # merge into bursts
    clusters: list[list[int]] = [[int(bad[0])]]
    for b in bad[1:]:
        if b - clusters[-1][-1] <= merge:
            clusters[-1].append(int(b))
        else:
            clusters.append([int(b)])
    out = x.copy()
    repaired: list[tuple[float, int]] = []
    n = len(mono)
    for cluster in clusters:
        a = max(1, cluster[0] - 5)
        b = min(n - 1, cluster[-1] + 5)
        if b - a < 4:
            continue
        idx = np.arange(a, b + 1)
        for ch in range(out.shape[1]):
            out[idx, ch] = np.interp(idx, [a, b], [out[a, ch], out[b, ch]]).astype(np.float32)
        repaired.append((cluster[0] / sr, len(cluster)))
    return out, repaired


# Broadcast voice curve for the placement copy: the delivered narration is very
# heavy below 120 Hz and light in the intelligibility band, so the mix lifts
# presence and clears the rumble. This is a mix decision, applied in memory --
# the approved MP3 is never touched, and --no-vo-eq bypasses it entirely.
VO_EQ = ((28.0, -18.0), (55.0, -13.0), (85.0, -9.0), (120.0, -5.0),
         (200.0, -2.0), (350.0, 0.0), (800.0, 1.5), (1600.0, 3.5),
         (3000.0, 5.0), (5000.0, 4.0), (8000.0, 2.0), (15000.0, 0.0))


def eq_curve(x: np.ndarray, sr: int = SR,
             points: tuple[tuple[float, float], ...] = ()) -> np.ndarray:
    """Zero-phase EQ: a smooth gain curve applied in the frequency domain.

    Points are (Hz, dB) and are interpolated on a log-frequency axis, so the
    curve is smooth and there is no phase shift to smear transients.
    """
    if not points:
        return x
    n = x.shape[0]
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    pf = np.array([max(p[0], 1.0) for p in points], np.float64)
    pg = np.array([p[1] for p in points], np.float64)
    db = np.interp(np.log10(np.maximum(freqs, 1.0)), np.log10(pf), pg,
                   left=pg[0], right=pg[-1])
    gain = (10.0 ** (db / 20.0)).astype(np.float32)
    spec = np.fft.rfft(x, axis=0)
    spec *= gain if spec.ndim == 1 else gain[:, None]
    return np.fft.irfft(spec, n=n, axis=0).astype(np.float32)


def duck_gain(vo: np.ndarray, sr: int, depth_db: float = -6.5,
              attack: float = 0.06, release: float = 0.55) -> np.ndarray:
    """Sidechain envelope from the voice-over: 1.0 in gaps, ducked under speech."""
    mono = np.abs(vo).max(axis=1)
    win = max(2, int(0.02 * sr))
    env = np.convolve(mono, np.ones(win, np.float32) / win, mode="same")
    thr = max(float(np.percentile(env, 92)) * 0.10, 1e-5)
    target = np.where(env > thr, 10.0 ** (depth_db / 20.0), 1.0).astype(np.float32)
    a = math.exp(-1.0 / (attack * sr))
    r = math.exp(-1.0 / (release * sr))
    out = np.empty_like(target)
    cur = 1.0
    for i, want in enumerate(target):
        coeff = a if want < cur else r
        cur = coeff * cur + (1.0 - coeff) * want
        out[i] = cur
    return out


def _window_db(signal: np.ndarray, sr: int, win: float = 0.25) -> np.ndarray:
    """Broadband level per window, in dBFS (mono sum of the stereo pair)."""
    mono = np.abs(signal).max(axis=1) if signal.ndim == 2 else np.abs(signal)
    n = max(1, int(win * sr))
    usable = (mono.shape[0] // n) * n
    if usable < n:
        return np.array([-120.0], np.float32)
    frames = mono[:usable].reshape(-1, n)
    rms = np.sqrt((frames ** 2).mean(axis=1))
    return 20.0 * np.log10(np.maximum(rms, 1e-8))


def calibrate_music(vo: np.ndarray, score: np.ndarray, sr: int = SR,
                    offset_db: float = -9.0) -> tuple[float, dict]:
    """Gain (dB) for the bed, set from the level of the narration.

    The music is not balanced against the voice *while both play* -- the ducker
    does that. It is set so that in the gaps, where nothing else is happening,
    the bed sits ``offset_db`` below the level of the narration. That keeps the
    quiet scenes quiet by design and keeps the end card audible, which a
    whole-mix average would destroy.
    """
    vo_db = _window_db(vo, sr)
    sc_db = _window_db(score, sr)
    n = min(len(vo_db), len(sc_db))
    if n < 8:
        return -18.0, {}
    vo_db, sc_db = vo_db[:n], sc_db[:n]
    speech_level = float(np.percentile(vo_db, 97))
    speech = vo_db > (speech_level - 26.0)
    gaps = ~speech
    if gaps.sum() < 8:
        gaps = vo_db < (speech_level - 40.0)
    score_gaps = float(np.median(sc_db[gaps])) if gaps.sum() else float(np.median(sc_db))
    gain = (speech_level + offset_db) - score_gaps
    return gain, {
        "vo_speech_peak_window_db": round(speech_level, 2),
        "score_median_in_gaps_db": round(score_gaps, 2),
        "offset_db": offset_db,
    }


def mix_film(vo: np.ndarray, score: np.ndarray, sr: int = SR,
             offset_db: float = -9.0, duck_db: float = -7.5,
             score_trim_db: float = 0.0) -> tuple[np.ndarray, dict]:
    """Voice-over at unity, score calibrated underneath, ducked, then summed."""
    n = max(len(vo), len(score))
    v = np.zeros((n, 2), np.float32)
    m = np.zeros((n, 2), np.float32)
    v[: len(vo)] = vo
    m[: len(score)] = score

    music_gain_db, calib = calibrate_music(v, m, sr, offset_db)
    music_gain_db += score_trim_db
    duck = duck_gain(v, sr, depth_db=duck_db)

    mixed = v + m * (10.0 ** (music_gain_db / 20.0)) * duck[:, None]
    peak = float(np.abs(mixed).max())
    if peak > 0.999:
        mixed *= 0.999 / peak
        calib["mix_pre_peak_limited"] = round(peak, 3)
    calib["music_gain_db"] = round(music_gain_db, 2)
    calib["duck_db"] = duck_db
    return mixed, calib


def measure_loudness(stereo: np.ndarray, sr: int = SR) -> float:
    """Integrated loudness in LUFS, measured by FFmpeg's EBU R128 meter."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        path = Path(handle.name)
    try:
        write_wav(path, stereo, sr)
        cmd = [ffmpeg_exe(), "-hide_banner", "-nostats", "-i", str(path),
               "-af", "ebur128=peak=true", "-f", "null", "-"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        tail = proc.stderr[proc.stderr.rfind("Summary:"):]
        integrated = None
        for line in tail.splitlines():
            line = line.strip()
            if line.startswith("I:"):
                integrated = float(line.split()[1])
        if integrated is None:
            raise RuntimeError("could not measure loudness:\n" + tail[-800:])
        return integrated
    finally:
        path.unlink(missing_ok=True)


def normalize(stereo: np.ndarray, target_lufs: float = -16.0,
              ceiling_db: float = -2.4, sr: int = SR) -> tuple[np.ndarray, dict]:
    """Two-pass: measure, apply gain, limit the peaks, re-measure.

    ``ceiling_db`` is the sample-peak ceiling, deliberately set below the
    deliverable true-peak target: inter-sample peaks and the AAC encoder's own
    overshoot add roughly 1.4 dB, so a -2.4 dBFS sample ceiling lands at about
    -1.0 dBTP in the delivered file.
    """
    measured = measure_loudness(stereo, sr)
    gain_db = target_lufs - measured
    out = stereo * (10.0 ** (gain_db / 20.0))
    ceiling = 10.0 ** (ceiling_db / 20.0)
    # soft knee limiter -- the mix is already controlled, this only catches peaks
    peak = float(np.abs(out).max())
    if peak > ceiling:
        knee = ceiling * 0.82
        over = np.abs(out) > knee
        sign = np.sign(out)
        out = np.where(over, sign * (knee + (ceiling - knee) * np.tanh((np.abs(out) - knee) / (ceiling - knee))), out)
    final = measure_loudness(out, sr)
    # the limiter shaves a few tenths of a LU; one corrective pass brings the
    # delivered file onto the target instead of just near it
    if abs(final - target_lufs) > 0.25:
        correction = 10.0 ** ((target_lufs - final) / 20.0)
        out = out * correction
        peak = float(np.abs(out).max())
        if peak > ceiling:
            out *= ceiling / peak
        final = measure_loudness(out, sr)
    info = {
        "measured_lufs_before": round(measured, 2),
        "gain_db_applied": round(gain_db, 2),
        "measured_lufs_after": round(final, 2),
        "target_lufs": target_lufs,
        "true_peak_ceiling_db": ceiling_db,
        "peak_after": round(float(np.abs(out).max()), 4),
    }
    return out.astype(np.float32), info
