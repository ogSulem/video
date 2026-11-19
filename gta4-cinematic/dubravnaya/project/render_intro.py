"""Render the separate Dubravnaya intro, timed to the supplied music file.

The phrase markers are specific to the shared audio/gta 4 — main theme.m4a.
Only Dubravnaya's own photographs are used for its animated foregrounds.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
from intro_design import (
    ACCENT_FRAMES, BASE, FPS, H, MUSIC_ACCENTS, MUSIC_START, SCENES, W, build_scene,
)
from photos import PHOTO_NAMES, REPO, SHARED
from motion_art import INSET
from motion_render import figure_filters
from PIL import Image

FF = shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()
MUSIC = SHARED / 'audio' / 'gta 4 — main theme.m4a'
MUSIC_SHA256 = 'd7bd9c1928ea5c264f0ea524ef11fc86127915fe292a7340a7b76176c33e900c'
def hard_cut_before(index):
    """Show only one photo at a time, including at every beat-marked cut.

    The same person may appear in adjacent photos. Mixing or wiping those
    shots together would create a visible duplicate even with distinct images.
    """
    return index > 0


def run(args):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode:
        raise RuntimeError('FFmpeg failed:\n' + result.stderr[-8000:])
    return result


def validate():
    if not MUSIC.is_file():
        raise FileNotFoundError(MUSIC)
    if hashlib.sha256(MUSIC.read_bytes()).hexdigest() != MUSIC_SHA256:
        raise ValueError('The music file has changed; remeasure the edit markers before rendering.')
    if len(SCENES) != len(MUSIC_ACCENTS) or len(SCENES) != 18:
        raise ValueError('Expected one opening and seventeen photo scenes')
    if SCENES[0].photo is not None or SCENES[0].frames != round(3.5 * FPS) or SCENES[1].split != 'cut':
        raise ValueError('The Dubravnaya opening must cut to the first photo at 3.5 seconds')
    used = tuple(s.photo for s in SCENES if s.photo)
    originals = {p.stem for p in (BASE / 'originals').glob('*.jpeg')}
    if used != PHOTO_NAMES or set(used) != originals or len(set(used)) != 17:
        raise ValueError('Exactly the 17 Dubravnaya originals must appear once, in attachment order')
    checksums = {}
    for line in (BASE / 'project' / 'ORIGINALS.sha256').read_text(encoding='utf-8').splitlines():
        digest, filename = line.split(maxsplit=1)
        checksums[filename.strip().lstrip('*')] = digest
    if set(checksums) != {f'{name}.jpeg' for name in PHOTO_NAMES}:
        raise ValueError('Originals checksum manifest does not match the 17-photo list')
    for filename, digest in checksums.items():
        if hashlib.sha256((BASE / 'originals' / filename).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Original photograph has changed: {filename}')
    elapsed = 0
    for s, frame, accent in zip(SCENES, ACCENT_FRAMES, MUSIC_ACCENTS):
        elapsed += s.frames
        if elapsed != frame or abs(frame / FPS - (accent - MUSIC_START)) > .5 / FPS + 1e-9:
            raise ValueError(f'Music marker out of frame tolerance: {s.key}')
        if s.frames < 16:
            raise ValueError(f'Scene too short for continuous motion: {s.key}')
        if s.split != 'cut':
            raise ValueError(f'Overlapping transitions could duplicate a person: {s.key}')
        if s.side not in ('left', 'right') or not 0 < s.crop <= 1:
            raise ValueError(f'Invalid figure framing: {s.key}')
        required = [SHARED/'assets'/'plates'/f'{s.plate}.jpg']
        if s.photo:
            required += [SHARED/'assets'/'plates'/f'{INSET[s.plate]}.jpg',
                         BASE/'processed'/f'{s.photo}_gta4.jpg',
                         BASE/'assets'/'motion_masks'/f'{s.photo}.png']
        for path in required:
            if not path.is_file():
                raise FileNotFoundError(path)
        if s.photo:
            with Image.open(required[-1]) as mask:
                hist = mask.convert('L').histogram()
            if sum(hist[86:]) < 50 or hist[0] < 50:
                raise ValueError(f'Mask is empty or is an uncut photo: {s.photo}')
    font = SHARED / 'assets' / 'fonts' / 'Anton-Regular.ttf'
    if not font.is_file():
        raise FileNotFoundError(font)


def render_scene(scene, index, output, art):
    background, foreground, title = build_scene(scene, index, art)
    frames = scene.frames
    cmd = [FF, '-hide_banner', '-loglevel', 'error', '-y', '-filter_complex_threads', '1',
           '-loop', '1', '-framerate', str(FPS), '-i', str(background)]
    if foreground:
        cmd += ['-loop', '1', '-framerate', str(FPS), '-i', str(foreground)]
    if title:
        cmd += ['-loop', '1', '-framerate', str(FPS), '-i', str(title)]

    # The background drifts independently of the person layer. The masked
    # foreground moves continuously from the first to the last frame.
    progress = f'on/{max(1, frames-1)}'
    zoom = f'1.018+0.045*({progress})' if index % 2 == 0 else f'1.063-0.045*({progress})'
    x = f'(iw-iw/zoom)*(.30+.40*({progress}))'
    graph = [(f'[0:v]scale={W}:{H},zoompan=z=\'{zoom}\':x=\'{x}\':'
              f'y=\'(ih-ih/zoom)/2\':d=1:s={W}x{H}:fps={FPS},setsar=1[bg]')]
    if foreground:
        graph += figure_filters(scene, index, foreground, frames)
    else:
        graph += ['[bg]null[composite]']
    if title:
        title_input = 2 if foreground else 1
        graph += [f'[{title_input}:v]format=rgba[type]',
                  '[composite][type]overlay=0:0:shortest=1:format=auto[framed]']
    else:
        graph += ['[composite]null[framed]']

    # No introductory fade: Dubravnaya is legible on the very first frame.
    # Only the final photo fades to black; no separate closing title is added.
    fade = ''
    if scene == SCENES[-1]:
        fade_frames = 30
        fade = f',fade=t=out:st={(frames-fade_frames)/FPS:.9f}:d={fade_frames/FPS:.9f}'
    graph += [f'[framed]null{fade},scale=iw:ih:in_range=full:out_range=tv,format=yuv420p,'
              'setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709[out]']
    # A low CRF and the medium preset retain more fine detail than the faster
    # draft encode; yuv420p keeps the MP4 broadly playable on common devices.
    cmd += ['-filter_complex', ';'.join(graph), '-map', '[out]', '-frames:v', str(frames), '-an',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-threads', '2',
            '-pix_fmt', 'yuv420p', '-r', str(FPS), '-color_range', 'tv',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', str(output)]
    run(cmd)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test-scenes', type=int, default=0,
                        help='render the first N scenes into .qc/dubravnaya/intro_test.mp4')
    args = parser.parse_args()
    if not 0 <= args.test_scenes <= len(SCENES):
        parser.error('--test-scenes out of range')
    validate()
    shots = SCENES[:args.test_scenes] if args.test_scenes else SCENES
    root = REPO / '.cache'
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='dubravnaya-intro-', dir=root) as tmp:
        tmp = Path(tmp)
        clips = []
        for i, scene in enumerate(shots):
            clip = tmp / f'shot_{i:02d}.mp4'
            print(f'Rendering {i+1:02}/{len(shots)} {scene.key} ({scene.frames/FPS:.3f}s)', flush=True)
            render_scene(scene, i, clip, tmp / 'art')
            clips.append(clip)
        # The clips have matching codec settings and are joined without overlap
        # or another generation of lossy video encoding. Each boundary is a
        # single musical cut, so there cannot be two photographs in one frame.
        total_frames = sum(s.frames for s in shots)
        listing = tmp / 'list.txt'
        listing.write_text(''.join(f"file '{clip.as_posix()}'\n" for clip in clips), encoding='utf-8')
        silent = tmp / 'silent.mp4'
        run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0',
             '-i', str(listing), '-map', '0:v:0', '-c', 'copy', str(silent)])
        duration = total_frames / FPS
        dest = (REPO / '.qc' / 'dubravnaya' / 'intro_test.mp4' if args.test_scenes
                else BASE / 'output' / 'dubravnaya_intro.mp4')
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Trim the lead-in so the first repeated percussion attack (4.840 s
        # in the source) lands on the first photo at 3.500 s. A brief fade-in
        # prevents a click at the trim point; it does not affect the attack.
        # Fixed attenuation leaves headroom without altering the dynamics.
        audio_filter = (f'atrim=start={MUSIC_START:.9f}:duration={duration:.9f},asetpts=PTS-STARTPTS,'
                        f'afade=t=in:st=0:d=0.08,volume=-5dB,'
                        f'afade=t=out:st={max(0, duration-2):.9f}:d=2,aresample=48000')
        completed = tmp / 'completed.mp4'
        run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(silent), '-i', str(MUSIC),
             '-map', '0:v:0', '-map', '1:a:0', '-filter:a', audio_filter, '-c:v', 'copy',
             '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-t', f'{duration:.9f}',
             '-metadata', 'title=Dubravnaya', '-movflags', '+faststart', str(completed)])
        completed.replace(dest)  # keep the previous export intact if rendering fails
        print(f'Saved {dest} — {duration:.3f}s, {total_frames} frames, {W}x{H}, {FPS}fps', flush=True)
        print('Every cut follows a music marker within one half-frame; photos never overlap.', flush=True)


if __name__ == '__main__':
    main()
