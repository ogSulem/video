#!/usr/bin/env python3
"""Render RETURN TO THE SLOPE — v5 review master.

Owner feedback: v4's dark end card is wrong. End like v2's good idea — the
camera flies into the sky (scene E) and the premium brand copy appears over
the sky, never over a dark card. All six generated scenes play at natural
speed joined by dissolves; NO optical flow (no jitter). Cut locked to the
approved Russian voice-over; ~76.44 s.

Everything local and deterministic; nothing approved is modified.
Output: video/final/altai_rehabilitation_v5.mp4
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "video"))

from filmkit import audio as film_audio   # noqa: E402
from filmkit.sources import verify        # noqa: E402

WIDTH, HEIGHT, FPS = 1920, 1080, 24
DISSOLVE = 0.35
FF = film_audio.ffmpeg_exe()

VOICEOVER = ROOT / "audio/voiceover/voiceover_ru_full_v1.mp3"
VO_SHA = "7d5368d3075ba16c30e9f6bf717d477c1ff2c6eb51bf59dba2a86b6d199376f1"

BRAND_NAME = "РЕАБИЛИТАЦИОННЫЙ ЦЕНТР АЛТАЙ"
TAGLINE = "Твой сезон продолжается."
WEBSITE = "altaysportreab.ru"

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

GRADE = {
    "cold":   "colorbalance=rs=-0.03:gs=-0.010:bs=0.025,vignette=PI/5,noise=alls=0.35:allf=t",
    "warm":   "colorbalance=rs=0.030:gs=0.000:bs=-0.020,vignette=PI/5,noise=alls=0.35:allf=t",
    "golden": "colorbalance=rs=0.040:gs=0.005:bs=-0.025,vignette=PI/5,noise=alls=0.35:allf=t",
}

# id, kind, source, in_seconds, dur_seconds, grade, name
SEGMENTS = [
    ("s0",  "clip", "scene a1.mp4",              0.0,  7.50, "cold",  "opening carve / freedom"),
    ("s1",  "clip", "scene a2.mp4",              0.0,  4.00, "cold",  "the fall"),
    ("s2",  "still", "references/scenes/REF-SCENE-02-injury-aftermath-v2.png", None, 4.00, "cold", "seated aftermath / silence"),
    ("s3",  "clip", "scene b.mp4",               1.0,  8.50, "cold",  "arrival at the centre"),
    ("s4",  "still", "references/scenes/REF-SCENE-04-reception-welcome.png",   None, 3.50, "warm", "reception welcome"),
    ("s5",  "clip", "scene c.mp4",               1.0,  8.50, "warm",  "biomechanics assessment"),
    ("s6",  "still", "references/scenes/REF-SCENE-07-recovery-physiotherapy.png", None, 3.50, "warm", "guided knee mobility"),
    ("s7",  "still", "references/scenes/REF-SCENE-06-rehabilitation-exercises.png", None, 3.50, "warm", "controlled movement"),
    ("s8",  "still", "references/scenes/REF-SCENE-08-rehabilitation-team.png",   None, 3.50, "warm", "team support"),
    ("s9",  "still", "references/scenes/REF-SCENE-10-final-brand-card.png",    None, 4.00, "golden", "each their own route / valley"),
    ("s10", "clip", "scene d.mp4",               0.0, 10.00, "golden","return carve"),
    ("s11", "clip", "scene e.mp4",               0.0, 10.12, "golden","camera flies into sky (held to end)"),
    ("s12", "still", "video/assets/endcard_v4_sky.png",                        None, 9.67, "golden", "premium text over sky"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_voiceover() -> Path:
    path = ROOT / "audio/voiceover/voiceover_ru_full_v1.mp3"
    actual = sha256(path)
    if actual != VO_SHA:
        raise RuntimeError(f"voice-over hash drifted: expected {VO_SHA}, got {actual}")
    return path


def segment_output_path(seg_id: str, tmp: Path) -> Path:
    return tmp / f"seg_{seg_id}.mp4"


def build_segment_filters(seg, total_seconds: float) -> str:
    _id, kind, source, in_s, dur, grade, _name = seg
    g = GRADE[grade]
    parts: list[str] = []
    if kind == "clip":
        parts.append(f"trim=start={in_s}:end={in_s + dur}")
        parts.append("setpts=PTS-STARTPTS")
    parts.append(f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase")
    parts.append(f"crop={WIDTH}:{HEIGHT}")
    if kind == "still":
        parts.append(
            f"zoompan=z='min(zoom+0.0010,1.10)':x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':s={WIDTH}x{HEIGHT}:fps={FPS}:d={int(round(total_seconds * FPS))}"
        )
    parts.append(g)
    return ",".join(parts)


def render_segment(seg, tmp: Path) -> tuple[Path, float]:
    seg_id, kind, source, in_s, dur, grade, _name = seg
    out = segment_output_path(seg_id, tmp)
    if out.exists() and out.stat().st_size > 1000:
        print(f"  {seg_id} -> (cached) {out.name}")
        return out, dur
    extended = dur + DISSOLVE if seg_id != "s12" else dur
    input_opts = ["-loop", "1", "-framerate", str(FPS), "-t", f"{extended:.3f}"] if kind == "still" else []
    vf = build_segment_filters(seg, extended)
    if kind == "clip":
        vf += f",tpad=stop={extended:.3f}:stop_mode=clone"
    cmd = [FF, "-hide_banner", "-loglevel", "error", "-y", *input_opts,
           "-i", str(ROOT / source),
           "-an", "-vf", vf,
           "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-t", f"{extended:.3f}",
           str(out)]
    subprocess.run(cmd, cwd=ROOT, check=True)
    return out, dur


def compute_slots(durs: list[float]) -> list[float]:
    slots = [0.0]
    for d in durs[:-1]:
        slots.append(slots[-1] + d - DISSOLVE)
    return slots


def assemble_video(segment_files: list[Path], slots: list[float],
                   durs: list[float], total: float, out: Path) -> None:
    inputs: list[str] = []
    filter_parts: list[str] = []
    for i, f in enumerate(segment_files):
        inputs += ["-i", str(f)]
        filter_parts.append(f"[{i}:v]setpts=PTS-STARTPTS,fps={FPS}[v{i}];")

    n = len(segment_files)
    xfades = []
    for i in range(1, n):
        in_label = "v0" if i == 1 else f"acc{i-1}"
        xfades.append(
            f"[{in_label}][v{i}]"
            f"xfade=transition=dissolve:duration={DISSOLVE}:offset={slots[i]:.4f}"
            f"[acc{i}]"
        )
    chain = ",".join(xfades)
    last = f"acc{n-1}" if n > 1 else "v0"
    vf = "".join(filter_parts) + chain + f",[{last}]trim=start=0:end={total},setpts=PTS-STARTPTS[vout]"

    cmd = [FF, "-hide_banner", "-loglevel", "error", "-y", *inputs,
           "-filter_complex", vf,
           "-map", "[vout]",
           "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-t", f"{total:.3f}",
           str(out)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        print("FFMPEG STDERR (head):\n", proc.stderr[:2500])
        print("FFMPEG STDERR (tail):\n", proc.stderr[-1500:])
        raise RuntimeError(f"xfade assembly failed (exit {proc.returncode})")


def render_bed(duration: float, tmp: Path) -> Path:
    sr = film_audio.SR
    n = int(round(duration * sr))
    t = np.arange(n, dtype=np.float32) / sr
    rng = np.random.default_rng(11)
    bed_l = np.zeros(n, np.float32)
    bed_r = np.zeros(n, np.float32)

    def midi_hz(note: float) -> float:
        return 440.0 * 2.0 ** ((note - 69.0) / 12.0)

    chords = [
        (0.0, 13.0, [57, 60, 64, 67, 71]),
        (13.0, 26.0, [52, 59, 62, 67, 71]),
        (26.0, 39.0, [53, 57, 60, 64, 67]),
        (39.0, 52.0, [48, 55, 59, 62, 64]),
        (52.0, 65.0, [57, 60, 64, 67, 72]),
        (65.0, duration, [48, 55, 59, 62, 64]),
    ]
    for st, en, notes in chords:
        f0 = max(0, int(st * sr)); f1 = min(n, int(en * sr))
        if f1 <= f0:
            continue
        seg = t[f0:f1] - st
        env = (np.clip(seg / 1.6, 0, 1) ** 1.6) * (np.clip((en - st - seg) / 1.9, 0, 1) ** 1.3)
        for note in notes:
            f = midi_hz(note)
            for cents, pan in ((0.0, 0.5), (6.0, 0.35), (-6.0, 0.65)):
                ff = f * 2.0 ** (cents / 1200.0)
                ph = float(rng.uniform(0, 2 * np.pi))
                w = (np.sin(2 * np.pi * ff * seg + ph)
                     + 0.30 * np.sin(2 * np.pi * ff * 2.0 * seg + ph * 0.7))
                w /= 1.7
                lfo = 1.0 + 0.08 * np.sin(2 * np.pi * (0.06 + 0.04 * pan) * seg + ph)
                w = w * lfo * env * 0.035
                bed_l[f0:f1] += w * (1.0 - pan)
                bed_r[f0:f1] += w * pan

    for on in np.arange(26.0, 62.0, 1.6):
        f0 = int(on * sr)
        if f0 >= n:
            break
        f1 = min(n, f0 + int(0.4 * sr))
        seg = t[f0:f1] - on
        env = (1.0 - np.exp(-seg / 0.008)) * np.exp(-seg / 0.17)
        thump = 0.014 * np.sin(2 * np.pi * 54.0 * seg) * env
        bed_l[f0:f1] += thump
        bed_r[f0:f1] += thump * 0.92

    bed = np.stack([bed_l, bed_r], axis=1)
    path = tmp / "bed.wav"
    film_audio.write_wav(path, bed, sr)
    return path


def render_audio(shots_total: float, tmp: Path) -> Path:
    vo_path = verify_voiceover()
    vo = film_audio.decode_voiceover(vo_path)

    bed_path = render_bed(shots_total, tmp)
    bed = film_audio.decode_voiceover(bed_path)

    n = max(len(vo), len(bed))
    v = np.zeros((n, 2), np.float32); m = np.zeros((n, 2), np.float32)
    v[:len(vo)] = vo
    m[:len(bed)] = bed

    music_gain_db, calib = film_audio.calibrate_music(v, m, film_audio.SR, -9.0)
    duck = film_audio.duck_gain(v, film_audio.SR, depth_db=-7.5)
    mixed = v + m * (10.0 ** (music_gain_db / 20.0)) * duck[:, None]
    peak = float(np.abs(mixed).max())
    if peak > 0.999:
        mixed *= 0.999 / peak

    mix_path = tmp / "mix_pre.wav"
    film_audio.write_wav(mix_path, mixed, film_audio.SR)
    mastered, info = film_audio.normalize(mixed)
    out_path = tmp / "mix.wav"
    film_audio.write_wav(out_path, mastered, film_audio.SR)
    return out_path, info


def mux_master(picture: Path, audio: Path, out: Path) -> None:
    cmd = [FF, "-hide_banner", "-loglevel", "error", "-y",
           "-i", str(picture), "-i", str(audio),
           "-map", "0:v:0", "-map", "1:a:0",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-shortest", "-movflags", "+faststart",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-metadata", "title=RETURN TO THE SLOPE — rehabilitation centre Altai (v5)",
           "-metadata", "comment=Smooth cut: generated scenes at natural speed, dissolves, "
                          "no optical-flow retiming; premium brand text over sky; locked Russian VO.",
           str(out)]
    subprocess.run(cmd, cwd=ROOT, check=True)


def probe(path: Path) -> None:
    cmd = [FF, "-hide_banner", "-i", str(path)]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).stderr
    for line in out.splitlines():
        if "Duration" in line or "Video:" in line or "Audio:" in line:
            print(line.strip())


def main() -> int:
    tmp = ROOT / ".qc" / "v5"
    tmp.mkdir(parents=True, exist_ok=True)
    out_dir = ROOT / "video" / "final"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "altai_rehabilitation_v5.mp4"

    print("verifying locked voice-over")
    verify_voiceover()
    print("  ok voice-over byte-identical")

    durs = [s[4] for s in SEGMENTS]
    slots = compute_slots(durs)
    total = slots[-1] + durs[-1]
    print(f"\nplan: {len(SEGMENTS)} segments, total {total:.2f}s, dissolve {DISSOLVE}s")
    for seg, slot, dur in zip(SEGMENTS, slots, durs):
        print(f"  {seg[0]:4s} {seg[1]:5s} slot={slot:6.2f} dur={dur:5.2f}  {seg[6]}")

    print("\n[1/4] rendering segments")
    segment_files: list[Path] = []
    for seg in SEGMENTS:
        f, dur = render_segment(seg, tmp)
        segment_files.append(f)

    picture = tmp / "picture.mp4"
    print(f"\n[2/4] assembling with dissolves -> {total:.2f}s")
    assemble_video(segment_files, slots, durs, total, picture)
    print(f"  wrote {picture.name} ({picture.stat().st_size:,} bytes)")

    print("\n[3/4] mixing audio")
    mix_path, info = render_audio(total, tmp)
    print(f"  loudness: {info}")

    print("\n[4/4] muxing master (premium text over sky)")
    mux_master(picture, mix_path, out_path)
    print(f"\nmaster: {out_path}")
    print(f"size:   {out_path.stat().st_size:,} bytes")
    print(f"sha256: {sha256(out_path)}")
    probe(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
