"""Audit every decoded frame and the full stereo soundtrack of an intro.

This supplements the visual/contact-sheet and optical-flow checks. It verifies
frame presentation timestamps and exact repeats, detects black gaps, and
compares one-second windows of both encoded channels with the provided music.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np


def _run(ff: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([ff, *map(str, args)], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _stereo(ff: str, path: Path, seconds: float, sr: int) -> np.ndarray:
    result = _run(ff, '-v', 'error', '-i', str(path), '-t', f'{seconds:.6f}',
                  '-vn', '-ac', '2', '-ar', str(sr), '-f', 'f32le', '-')
    return np.frombuffer(result.stdout, dtype='<f4').reshape(-1, 2).astype(np.float64)


def verify_continuity(video: Path, music: Path, ff: str, fps: int,
                      expected_frames: int, music_start: float) -> None:
    """Raise on incorrect frame times, repeated pictures, black gaps or audio gaps."""
    # showinfo reports the presentation time and a checksum of each decoded
    # frame; blackdetect considers a frame black when at least 98% of its
    # pixels are below 10% luminance, for at least 0.2 seconds.
    result = _run(ff, '-hide_banner', '-nostats', '-loglevel', 'info', '-i', str(video),
                  '-an', '-vf', 'showinfo,blackdetect=d=0.2:pic_th=0.98:pix_th=0.10',
                  '-fps_mode', 'passthrough', '-f', 'null', '-')
    text = result.stderr.decode('utf-8', 'replace')
    pattern = re.compile(r'\bn:\s*(\d+)\s+pts:\s*\d+\s+pts_time:([\d.]+).*?checksum:([0-9A-F]+)')
    samples = pattern.findall(text)
    if len(samples) != expected_frames:
        raise ValueError(f'Continuity scan found {len(samples)} frames; expected {expected_frames}')
    repeated = []
    previous = None
    max_error = 0.0
    for expected, (number, timestamp, checksum) in enumerate(samples):
        if int(number) != expected:
            raise ValueError(f'Frame index {number} is not sequential at {expected}')
        error = abs(float(timestamp) - expected/fps)
        max_error = max(max_error, error)
        if error > .001:
            raise ValueError(f'Unexpected frame timestamp at {expected}: {timestamp}')
        if checksum == previous:
            repeated.append(expected)
        previous = checksum
    if repeated:
        raise ValueError(f'Exact repeated frames found: {repeated[:20]}')
    blacks = re.findall(r'black_start:[^\n]+', text)
    if blacks:
        raise ValueError('Unexpected black interval: ' + '; '.join(blacks))
    print(f'  {expected_frames} frame timestamps checked; maximum error {max_error*1000:.3f} ms; '
          'no exact repeated frames or black intervals >= 0.2s.', flush=True)

    # Compare every second of both channels separately. Exclude the intentional
    # 80 ms fade-in and last 2 s fade-out; they have time-varying gain. A low
    # energy reference is skipped because correlation then has no meaning.
    sr = 16000
    duration = expected_frames / fps
    reference = _stereo(ff, music, music_start + duration + .1, sr)
    output = _stereo(ff, video, duration + .1, sr)
    if abs(len(output) - round(duration*sr)) > 1024:
        raise ValueError(f'Unexpected audio duration: {len(output)/sr:.4f}s; expected {duration:.4f}s')
    source_offset = round(music_start*sr)
    correlations = []
    gains = []
    for sec in range(1, int(duration-2)):
        start = sec*sr
        source = reference[source_offset+start:source_offset+start+sr]
        decoded = output[start:start+sr]
        if source.shape != (sr, 2) or decoded.shape != (sr, 2):
            raise ValueError(f'Incomplete stereo audio near {sec}s')
        for channel in (0, 1):
            ref, got = source[:, channel], decoded[:, channel]
            energy = float(np.dot(ref, ref))
            actual = float(np.dot(got, got))
            if energy < sr*1e-9:
                continue
            cross = float(np.dot(ref, got))
            similarity = cross / np.sqrt(max(energy*actual, 1e-30))
            gain = cross / energy
            if similarity < .95 or not .50 < gain < .63:
                raise ValueError(f'Audio mismatch at {sec}s channel {channel}: '
                                 f'correlation {similarity:.4f}, gain {gain:.4f}')
            correlations.append(similarity)
            gains.append(gain)
    if not correlations:
        raise ValueError('No non-silent soundtrack windows could be compared')
    print(f'  {len(correlations)} one-second channel windows: minimum correlation '
          f'{min(correlations):.4f}, gain {min(gains):.4f}–{max(gains):.4f}; '
          'both channels follow the source without gaps.', flush=True)
