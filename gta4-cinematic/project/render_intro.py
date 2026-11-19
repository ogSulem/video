"""Render the Spartak photo intro, timed to the supplied music file.

The phrase markers are specific to audio/gta 4 — main theme.m4a. Replacing
that file without rebuilding the timing grid would not preserve beat sync.
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
from process_photos import NEW_PHOTOS

FF = shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()
MUSIC = BASE / 'audio' / 'gta 4 — main theme.m4a'
MUSIC_SHA256 = 'd7bd9c1928ea5c264f0ea524ef11fc86127915fe292a7340a7b76176c33e900c'
TRANSITION_FRAMES = 8
HALF_TRANSITION = TRANSITION_FRAMES // 2
GROUP_SIZE = 5


def hard_cut_before(index):
    """Keep the opening entirely on screen until the first musical attack.

    Later hard cuts divide rendering into manageable groups. Other boundaries
    use the incoming scene's eight-frame dissolve or slide.
    """
    return index == 1 or (index > 1 and (index - 1) % GROUP_SIZE == 0)


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
    if len(SCENES) != len(MUSIC_ACCENTS) or len(SCENES) != 21:
        raise ValueError('Expected one opening and twenty photo scenes')
    if SCENES[0].photo is not None or SCENES[0].frames != round(3.5 * FPS) or SCENES[1].split != 'cut':
        raise ValueError('The Spartak opening must cut to the first photo at 3.5 seconds')
    if {s.photo for s in SCENES[1:5]} != {Path(name).stem for name in NEW_PHOTOS}:
        raise ValueError('The four new photos must immediately follow the opening')
    elapsed = 0
    for s, frame, accent in zip(SCENES, ACCENT_FRAMES, MUSIC_ACCENTS):
        elapsed += s.frames
        if elapsed != frame or abs(frame / FPS - (accent - MUSIC_START)) > .5 / FPS + 1e-9:
            raise ValueError(f'Music marker out of frame tolerance: {s.key}')
        if s.frames < TRANSITION_FRAMES * 2:
            raise ValueError(f'Scene too short for its transition: {s.key}')
        required = [BASE / 'assets' / 'plates' / f'{s.plate}.jpg']
        if s.photo:
            required += [BASE / 'processed' / f'{s.photo}_gta4.jpg',
                         BASE / 'assets' / 'cinematic_16x9' / f'{s.photo}_16x9.jpg',
                         BASE / 'assets' / 'intro_masks' / f'{s.photo}.png']
        for path in required:
            if not path.is_file():
                raise FileNotFoundError(path)
    originals = {p.stem for p in (BASE / 'originals').glob('*.jpeg')}
    used = [s.photo for s in SCENES if s.photo]
    if len(used) != 20 or len(set(used)) != 20 or set(used) != originals:
        raise ValueError('All twenty original photos must appear exactly once')
    font = BASE / 'assets' / 'fonts' / 'Anton-Regular.ttf'
    if not font.is_file():
        raise FileNotFoundError(font)


def render_scene(scene, index, output, art, head, tail):
    background, foreground, title = build_scene(scene, index, art)
    frames = scene.frames + head + tail
    seconds = frames / FPS
    cmd = [FF, '-hide_banner', '-loglevel', 'error', '-y', '-filter_complex_threads', '1',
           '-loop', '1', '-framerate', str(FPS), '-i', str(background)]
    if foreground:
        cmd += ['-loop', '1', '-framerate', str(FPS), '-i', str(foreground)]
    if title:
        cmd += ['-loop', '1', '-framerate', str(FPS), '-i', str(title)]

    # d=1: a looped still must yield one video frame per input frame, not a
    # full clip per still. Both motion and transition durations are frame-based.
    progress = f'on/{max(1, frames-1)}'
    zoom = f'1.018+0.025*({progress})' if index % 2 == 0 else f'1.043-0.025*({progress})'
    x = '(iw-iw/zoom)*.42' if scene.side == 'right' else '(iw-iw/zoom)*.58'
    graph = [(f'[0:v]scale={W}:{H},zoompan=z=\'{zoom}\':x=\'{x}\':'
              f'y=\'(ih-ih/zoom)/2\':d=1:s={W}x{H}:fps={FPS},setsar=1[bg]')]
    if foreground:
        sign = 1 if scene.side == 'right' else -1
        # The cutout is present from the first frame of the transition instead
        # of fading in after the beat. Its small entrance movement settles fast.
        xpos = f'if(lt(t,0.20),{sign}*36*(1-t/0.20),0)+{sign}*12*t/{seconds:.6f}'
        graph += ['[1:v]format=rgba[figure]',
                  f"[bg][figure]overlay=x='{xpos}':y=0:shortest=1:format=auto[composite]"]
    else:
        graph += ['[bg]null[composite]']
    if title:
        title_input = 2 if foreground else 1
        graph += [f'[{title_input}:v]format=rgba[type]',
                  '[composite][type]overlay=0:0:shortest=1:format=auto[framed]']
    else:
        graph += ['[composite]null[framed]']

    # No introductory fade: Spartak is legible on the very first frame.
    # Only the final photo fades to black; no separate closing title is added.
    fade = ''
    if scene.key == 'portrait':
        fade_frames = 30
        fade = f',fade=t=out:st={(frames-fade_frames)/FPS:.9f}:d={fade_frames/FPS:.9f}'
    graph += [f'[framed]null{fade},scale=iw:ih:in_range=full:out_range=tv,format=yuv420p,'
              'setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709[out]']
    cmd += ['-filter_complex', ';'.join(graph), '-map', '[out]', '-frames:v', str(frames), '-an',
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-threads', '2',
            '-pix_fmt', 'yuv420p', '-r', str(FPS), '-color_range', 'tv',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', str(output)]
    run(cmd)


def render_group(shots, clips, output, group_index):
    if any(shot.split == 'cut' for shot in shots[1:]):
        raise ValueError('A hard cut must begin a separate rendering group')
    cmd = [FF, '-hide_banner', '-loglevel', 'error', '-y', '-filter_complex_threads', '1']
    for clip in clips:
        cmd += ['-i', str(clip)]
    filters = [f'[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[v{i}]' for i in range(len(clips))]
    prev = 'v0'
    elapsed = shots[0].frames
    for i in range(1, len(shots)):
        # Extend both clips by half a transition. A dissolve/slide starts four
        # frames before the musical marker, so its visual midpoint is on it.
        offset = (elapsed - HALF_TRANSITION) / FPS
        filters.append(f'[{prev}][v{i}]xfade=transition={shots[i].split}:'
                       f'duration={TRANSITION_FRAMES/FPS:.9f}:offset={offset:.9f}[vout{i}]')
        prev = f'vout{i}'
        elapsed += shots[i].frames
    filters.append(f'[{prev}]format=yuv420p[out]')
    cmd += ['-filter_complex', ';'.join(filters), '-map', '[out]', '-frames:v', str(elapsed), '-an',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-threads', '2',
            '-pix_fmt', 'yuv420p', '-r', str(FPS), '-color_range', 'tv',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', str(output)]
    print(f'Combining section {group_index + 1} ({elapsed/FPS:.3f}s)', flush=True)
    run(cmd)
    return elapsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test-scenes', type=int, default=0,
                        help='render the first N scenes only into .qc/intro_test.mp4')
    args = parser.parse_args()
    if not 0 <= args.test_scenes <= len(SCENES):
        parser.error('--test-scenes out of range')
    validate()
    shots = SCENES[:args.test_scenes] if args.test_scenes else SCENES
    root = BASE.parent / '.cache'
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='spartak-intro-', dir=root) as tmp:
        tmp = Path(tmp)
        clips = []
        for i, scene in enumerate(shots):
            clip = tmp / f'shot_{i:02d}.mp4'
            head = HALF_TRANSITION if i > 0 and not hard_cut_before(i) else 0
            tail = HALF_TRANSITION if i + 1 < len(shots) and not hard_cut_before(i + 1) else 0
            print(f'Rendering {i+1:02}/{len(shots)} {scene.key} ({scene.frames/FPS:.3f}s)', flush=True)
            render_scene(scene, i, clip, tmp / 'art', head, tail)
            clips.append(clip)
        groups = []
        total_frames = 0
        boundaries = [0] + [i for i in range(1, len(shots)) if hard_cut_before(i)] + [len(shots)]
        for group_index, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
            group = tmp / f'group_{group_index:02d}.mp4'
            total_frames += render_group(shots[start:end], clips[start:end], group, group_index)
            groups.append(group)
        listing = tmp / 'list.txt'
        listing.write_text(''.join(f"file '{g.as_posix()}'\n" for g in groups), encoding='utf-8')
        silent = tmp / 'silent.mp4'
        run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0',
             '-i', str(listing), '-map', '0:v:0', '-c', 'copy', str(silent)])
        duration = total_frames / FPS
        dest = (BASE.parent / '.qc' / 'intro_test.mp4' if args.test_scenes
                else BASE / 'output' / 'spartak_intro.mp4')
        dest.parent.mkdir(exist_ok=True)
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
             '-metadata', 'title=Spartak', '-movflags', '+faststart', str(completed)])
        completed.replace(dest)  # keep the previous export intact if rendering fails
        print(f'Saved {dest} — {duration:.3f}s, {total_frames} frames, {W}x{H}, {FPS}fps', flush=True)
        print('Cuts and transition midpoints follow the music markers within one half-frame.', flush=True)


if __name__ == '__main__':
    main()
