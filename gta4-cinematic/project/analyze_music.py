"""Recheck the phrase markers against the supplied slowed music track.

The first clearly repeated percussive accent (4.840 s) is used as an 80 ms
reference. Normalized correlation finds the same transient every eight beats.
A weaker/changed bar is reported as a grid estimate, not a detected transient.
"""
from __future__ import annotations

import subprocess
import numpy as np
from scipy.signal import butter, correlate, fftconvolve, sosfiltfilt
from intro_design import ACCENT_FRAMES, FPS, MUSIC_ACCENTS
from render_intro import FF, MUSIC, validate


def find_accents():
    sr = 22050
    r = subprocess.run([FF, '-v', 'error', '-i', str(MUSIC), '-t', '64',
                        '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    y = np.frombuffer(r.stdout, dtype='<f4').astype(np.float64)
    y = sosfiltfilt(butter(4, (300, 3000), btype='bandpass', fs=sr, output='sos'), y)
    reference_start, period, length = 4.8400, 3.6532, .080
    template = y[round(reference_start*sr):round((reference_start+length)*sr)]
    template /= np.linalg.norm(template)
    result = []
    for i in range(len(MUSIC_ACCENTS)):
        expected = reference_start + i * period
        start = round((expected-.085)*sr)
        end = round((expected+.085+length)*sr)
        window = y[start:end]
        similarity = correlate(window, template, mode='valid', method='fft')
        energy = np.sqrt(np.maximum(fftconvolve(window**2, np.ones(len(template)), mode='valid'), 1e-12))
        similarity /= energy
        j = int(np.argmax(similarity))
        confidence = float(similarity[j])
        # The beat at ~45.025 s has a different/weak attack. Its timing is
        # inferred from the surrounding pulse, rather than claiming detection.
        detected = confidence >= .35
        seconds = (start+j)/sr if detected else expected
        result.append((seconds, confidence, detected))
    return result


def main():
    validate()
    found = find_accents()
    print('Accent | seconds in source | frame / 24 fps | quantization error | match')
    for i, ((seconds, confidence, detected), frame, marker) in enumerate(zip(found, ACCENT_FRAMES, MUSIC_ACCENTS), 1):
        if abs(seconds-marker) > .006:
            raise ValueError(f'Measured music marker {i} differs from stored value: {seconds:.4f} vs {marker:.4f}')
        error = (frame/FPS-seconds)*1000
        kind = f'transient {confidence:.2f}' if detected else f'grid estimate (match {confidence:.2f})'
        print(f'{i:>6} | {seconds:>17.4f} | {frame:>5} / {frame/FPS:7.3f}s | {error:>+7.1f} ms | {kind}')


if __name__ == '__main__':
    main()
