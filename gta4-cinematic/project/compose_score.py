"""Compose a small original synth score precisely for this edit.

No existing GTA IV recording, tune, voice or external sample is used. The
90 BPM grid is exact at 24 fps (16 video frames/beat). The music is a
purpose-built stand-in until a desired original track is supplied.
"""
from __future__ import annotations
import math
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from scipy.signal import butter, sosfilt
from intro_design import BASE, FPS, BEAT_FRAMES, SCENES

SR = 48000
BEAT = BEAT_FRAMES / FPS  # 2/3 seconds, exactly 90 BPM
DURATION = sum(s.frames for s in SCENES) / FPS
RNG = np.random.default_rng(5808)


def frequency(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def put(mix, signal, at, pan=0.0):
    start = max(0, int(round(at * SR)))
    n = min(len(signal), len(mix) - start)
    if n <= 0:
        return
    # Equal-power stereo pan (-1 left, +1 right).
    theta = (pan + 1) * math.pi / 4
    mix[start:start+n, 0] += signal[:n] * math.cos(theta)
    mix[start:start+n, 1] += signal[:n] * math.sin(theta)


def pad_note(note, duration, amp=.055, detune=0):
    t = np.arange(round(duration * SR), dtype=np.float32) / SR
    f = frequency(note)
    attack = np.clip(t / 1.1, 0, 1)
    release = np.clip((duration - t) / 1.2, 0, 1)
    vibrato = 0.004 * np.sin(2*np.pi*.28*t + detune)
    tone = (np.sin(2*np.pi*f*t + vibrato) +
            .38*np.sin(2*np.pi*(f*1.002)*t + .4 + vibrato) +
            .16*np.sin(2*np.pi*(2*f)*t + .6))
    return (amp * tone * attack * release).astype(np.float32)


def pluck(note, length=2.2, amp=.09):
    t = np.arange(round(length * SR), dtype=np.float32)/SR
    f = frequency(note)
    envelope = (1-np.exp(-t*95)) * np.exp(-t*2.25)
    tone = (np.sin(2*np.pi*f*t) + .30*np.sin(2*np.pi*(2.01*f)*t)*np.exp(-t*2) +
            .14*np.sin(2*np.pi*(3.02*f)*t)*np.exp(-t*3))
    return (amp * envelope * tone).astype(np.float32)


def bass(note, length=1.1, amp=.16):
    t=np.arange(round(length*SR),dtype=np.float32)/SR
    env=(1-np.exp(-t*30))*np.exp(-t*2.3)
    f=frequency(note)
    tone=np.sin(2*np.pi*f*t)+.18*np.sin(2*np.pi*2*f*t)
    return (amp*env*tone).astype(np.float32)


def kick(amp=.25):
    t=np.arange(round(.55*SR),dtype=np.float32)/SR
    # Exponential pitch sweep, not a recording of a drum.
    phase=2*np.pi*(42*t + 80*.035*(1-np.exp(-t/.035)))
    body=np.sin(phase)*np.exp(-t*11)
    click=RNG.normal(0,1,len(t))*np.exp(-t*115)*.11
    return (amp*(body+click)).astype(np.float32)


def snare(amp=.075):
    n=round(.28*SR);t=np.arange(n,dtype=np.float32)/SR
    white=RNG.normal(0,1,n).astype(np.float32)
    filtered=sosfilt(butter(2,1300,fs=SR,btype="highpass",output="sos"),white).astype(np.float32)
    return (amp*(filtered*np.exp(-t*18)+.35*np.sin(2*np.pi*175*t)*np.exp(-t*20))).astype(np.float32)


def hat(amp=.018):
    n=round(.10*SR);t=np.arange(n,dtype=np.float32)/SR
    white=RNG.normal(0,1,n).astype(np.float32)
    filtered=sosfilt(butter(2,5500,fs=SR,btype="highpass",output="sos"),white).astype(np.float32)
    return amp*filtered*np.exp(-t*50)


def main():
    samples = round(DURATION * SR)
    mix = np.zeros((samples,2),dtype=np.float32)
    # Restrained rain-like texture; no recognisable third-party samples.
    noise=RNG.normal(0,1,samples).astype(np.float32)
    rain=sosfilt(butter(2,[1800,7000],fs=SR,btype="bandpass",output="sos"),noise).astype(np.float32)
    slow=.6+.4*np.sin(np.arange(samples,dtype=np.float32)/SR*.11)
    mix[:,0] += .005*rain*slow;mix[:,1] += .005*np.roll(rain,113)*slow
    del noise,rain,slow

    # D minor / Bb / F / C, 8 beats per chord; this is newly synthesized,
    # not a transcription of a GTA IV theme.
    chords=[(50,53,57),(46,50,53),(53,57,60),(48,52,55)]
    roots=[38,34,41,36]
    total_beats=round(DURATION/BEAT)
    for bar in range(math.ceil(total_beats/8)):
        when=bar*8*BEAT
        chord=chords[bar%4]
        for j,note in enumerate(chord):
            put(mix,pad_note(note,8*BEAT+.8,amp=.028,detune=j*.8),when,pan=(-.45,0,.45)[j])
        # Sparse repeating keys; the exact notes and rhythm are original.
        pattern=[(0,chord[0]+12), (2,chord[1]+12), (3.5,chord[2]+12),
                 (5,chord[1]+12), (7,chord[0]+12)]
        for beat,note in pattern:
            t=when+beat*BEAT
            sig=pluck(note,amp=.052 if when<5 else .066)
            put(mix,sig,t,pan=-.23 if beat%2==0 else .25)
            put(mix,sig*.22,t+.5*BEAT,pan=.35)
            put(mix,sig*.10,t+BEAT,pan=-.35)
        if when >= 5:
            for b in (0,4):
                put(mix,bass(roots[bar%4],amp=.12),when+b*BEAT)

    for beat in range(total_beats):
        t=beat*BEAT
        if beat >= 8 and t < DURATION-3:
            if beat%4 in (0,2): put(mix,kick(.21 if beat%4==0 else .17),t)
            if beat%4 in (1,3): put(mix,snare(.058),t,pan=.03)
            if beat%2==0: put(mix,hat(.016),t+.5*BEAT,pan=(-.28 if beat%4==0 else .28))

    # A short low impact on scene changes, quantized to the exact frame grid.
    frame=0
    for i,scene in enumerate(SCENES):
        if i and i not in (1,18):
            t=frame/FPS
            put(mix,kick(.07),t)
        frame += scene.frames

    # Fade in/out and normalize with gentle saturation; protect against clipping.
    envelope=np.ones(samples,dtype=np.float32)
    intro=round(.7*SR);outro=round(3*SR)
    envelope[:intro]=np.linspace(0,1,intro,dtype=np.float32)
    envelope[-outro:]=np.linspace(1,0,outro,dtype=np.float32)
    mix *= envelope[:,None]
    mix = np.tanh(mix*1.35)
    peak=float(np.max(np.abs(mix)))
    if peak > 0:
        mix *= min(2.0,.86/peak)
    print(f"score: {DURATION:.3f}s, 90 BPM, peak={np.max(np.abs(mix)):.3f}, RMS={np.sqrt(np.mean(mix*mix)):.4f}")
    pcm=(np.clip(mix,-1,1)*32767).astype('<i2')
    out=BASE/'audio'/'original_score_90bpm.m4a';out.parent.mkdir(exist_ok=True)
    ff=shutil.which('ffmpeg') or imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as tmp:
        wav=Path(tmp)/'score.wav'
        with wave.open(str(wav),'wb') as w:
            w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
        subprocess.run([ff,'-hide_banner','-loglevel','error','-y','-i',str(wav),'-c:a','aac','-b:a','160k',str(out)],check=True)
    print(f"wrote {out}")


if __name__=='__main__':
    main()
