"""Technical, music-alignment and transition checks for the finished intro."""
from pathlib import Path
import hashlib
import re
import subprocess
import sys

import numpy as np
from scipy.signal import correlate, fftconvolve
from PIL import Image, ImageDraw, ImageOps, ImageStat
from intro_design import ACCENT_FRAMES, BASE, FPS, H, MUSIC_ACCENTS, MUSIC_START, SCENES, W, title_layer
from render_intro import FF, MUSIC, hard_cut_before, validate
from analyze_music import find_accents


def ff(*args, check=True):
    return subprocess.run([FF, *map(str, args)], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=check)


def decoded_mono(path, sr=16000, seconds=72):
    audio = ff('-v', 'error', '-i', path, '-t', seconds, '-vn', '-ac', '1',
               '-ar', sr, '-f', 'f32le', '-').stdout
    return np.frombuffer(audio, dtype='<f4').astype(np.float64)


def verify_audio_alignment(video):
    sr = 16000
    source, output = decoded_mono(MUSIC), decoded_mono(video)
    maxlag = round(.2 * sr)
    # The first window straddles the opening's cut and the drum attack.
    for start in (2.9, 8.0, 25.0, 44.0, 62.0):
        first = round(start * sr)
        source_first = round((start + MUSIC_START) * sr)
        size = round(1.5 * sr)
        ref = source[source_first:source_first+size]
        candidate = output[first-maxlag:first+size+maxlag]
        if len(ref) != size or len(candidate) != size + 2*maxlag:
            raise ValueError('Audio is unexpectedly short')
        cross = correlate(candidate, ref, mode='valid', method='fft')
        energy = fftconvolve(candidate**2, np.ones(size), mode='valid')
        similarity = cross / np.sqrt(np.maximum(energy, 1e-12) * np.dot(ref, ref))
        best = int(np.argmax(similarity))
        lag = (best-maxlag) / sr
        if abs(lag) > .5/FPS or similarity[best] < .95:
            raise ValueError(f'Music does not match source at {start}s: lag {lag:.4f}, correlation {similarity[best]:.4f}')
        print(f'  music {start:4.1f}s: lag {lag*1000:+6.2f} ms, correlation {similarity[best]:.4f}')


def extract_selected_frames(video, frame_numbers):
    width, height = 320, 180
    frame_numbers = sorted(set(frame_numbers))
    # Compress contiguous frames into ranges; hundreds of nested eq() terms
    # can exceed FFmpeg's expression-parser recursion limit.
    ranges = []
    first = last = frame_numbers[0]
    for n in frame_numbers[1:]:
        if n == last + 1:
            last = n
        else:
            ranges.append((first, last))
            first = last = n
    ranges.append((first, last))
    select = '+'.join(f'eq(n,{a})' if a == b else f'between(n,{a},{b})' for a,b in ranges)
    data = ff('-v', 'error', '-i', video, '-an', '-vf',
              f"select='{select}',scale={width}:{height},format=rgb24",
              '-fps_mode', 'passthrough', '-f', 'rawvideo', '-c:v', 'rawvideo',
              '-threads', '1', '-').stdout
    frame_size = width*height*3
    if len(data) != frame_size*len(frame_numbers):
        raise ValueError(f'Expected {len(frame_numbers)} selected frames, got {len(data)//frame_size}')
    values = np.frombuffer(data, np.uint8).reshape(-1, height, width, 3)
    return {n: im for n, im in zip(frame_numbers, values)}


def verify_transitions_and_contact_sheet(video):
    starts = [0] + list(ACCENT_FRAMES[:-1])
    midpoints = [start + scene.frames//2 for start, scene in zip(starts, SCENES)]
    requested = [0, sum(s.frames for s in SCENES)-1, *midpoints]
    for b in ACCENT_FRAMES[:-1]:
        requested.extend(range(b-6, b+7))
    images = extract_selected_frames(video, requested)
    if ImageStat.Stat(Image.fromarray(images[0])).mean == [0, 0, 0]:
        raise ValueError('First frame is black; the Spartak title should be visible')
    if title_layer(SCENES[0]) is None or any(title_layer(s) is not None for s in SCENES[1:]):
        raise ValueError('Only the opening scene should have typography')

    for i, b in enumerate(ACCENT_FRAMES[:-1], start=1):
        shot = SCENES[i]
        if hard_cut_before(i):
            # Groups meet on a hard cut; no xfade is applied at this boundary.
            diffs = {n: np.abs(images[n].astype('float32') - images[n-1]).mean()
                     for n in range(b-3, b+4)}
            if max(diffs, key=diffs.get) != b:
                raise ValueError(f'Hard cut for {shot.key} is not at frame {b}: {diffs}')
            print(f'  frame {b:4} {shot.key:10} hard cut on marker')
        elif shot.split == 'fade':
            a = images[b-6].astype('float32')
            z = images[b+6].astype('float32')
            at = images[b].astype('float32')
            diff = z-a
            ratio = float(np.sum((at-a)*diff) / max(1.0, np.sum(diff*diff)))
            if not .32 <= ratio <= .68:
                raise ValueError(f'Dissolve midpoint for {shot.key} misses frame {b}: {ratio:.3f}')
            print(f'  frame {b:4} {shot.key:10} dissolve mix {ratio:.3f}')
        else:
            print(f'  frame {b:4} {shot.key:10} {shot.split} midpoint (see contact sheet)')

    qc = BASE.parent / '.qc'
    qc.mkdir(exist_ok=True)
    width, height, label, columns = 320, 180, 22, 4
    rows = (len(SCENES)+columns-1)//columns
    sheet = Image.new('RGB', (width*columns, (height+label)*rows), (8, 11, 12))
    draw = ImageDraw.Draw(sheet)
    for i, (s, n) in enumerate(zip(SCENES, midpoints)):
        image = Image.fromarray(images[n])
        if max(ImageStat.Stat(image).mean) < 2:
            raise ValueError(f'Unexpected black scene midpoint: {s.key}')
        x, y = (i%columns)*width, (i//columns)*(height+label)
        sheet.paste(image, (x,y))
        draw.text((x+5,y+height+3), f'{i+1:02} | {n/FPS:06.2f}s | {s.key}', fill='white')
    sheet.save(qc/'intro_contact_sheet.jpg', quality=90)

    # Before, on and after each transition. Used for manual inspection, too.
    transitions = Image.new('RGB', (width*3, (height+label)*(len(ACCENT_FRAMES)-1)), (8,11,12))
    draw = ImageDraw.Draw(transitions)
    for i, b in enumerate(ACCENT_FRAMES[:-1]):
        for col, n in enumerate((b-5,b,b+5)):
            x, y = col*width, i*(height+label)
            transitions.paste(Image.fromarray(images[n]), (x,y))
            draw.text((x+5,y+height+3), f'{SCENES[i+1].key} | frame {n}', fill='white')
    transitions.save(qc/'transition_contact_sheet.jpg', quality=90)
    Image.fromarray(images[0]).save(qc/'first_frame.jpg', quality=95)
    print(f'  visual sheets: {qc}/intro_contact_sheet.jpg and transition_contact_sheet.jpg')


def main():
    video = Path(sys.argv[1]) if len(sys.argv)>1 else BASE/'output'/'spartak_intro.mp4'
    if not video.is_file():
        raise FileNotFoundError(video)
    validate()
    originals = sorted((BASE/'originals').glob('*.jpeg'))
    for p in originals:
        processed = BASE/'processed'/f'{p.stem}_gta4.jpg'
        if not processed.exists():
            raise FileNotFoundError(processed)
        with Image.open(p) as src, Image.open(processed) as graded:
            if ImageOps.exif_transpose(src).size != graded.size:
                raise ValueError(f'Processed photo resolution differs: {p.name}')
    upload = Path('/tmp/arena-coding-uploads')
    if upload.is_dir() and all((upload/p.name).is_file() for p in originals):
        for p in originals:
            if hashlib.sha256(p.read_bytes()).digest() != hashlib.sha256((upload/p.name).read_bytes()).digest():
                raise ValueError(f'Original does not match upload: {p.name}')
        print(f'Original SHA-256 hashes match all {len(originals)} uploads.')
    print(f'{len(originals)} originals and full-resolution processed images; all included in edit.')

    expected = sum(s.frames for s in SCENES)/FPS
    text = ff('-hide_banner', '-i', video, check=False).stderr.decode('utf8', 'replace')
    vl = next((x.strip() for x in text.splitlines() if 'Video:' in x), '')
    al = next((x.strip() for x in text.splitlines() if 'Audio:' in x), '')
    match = re.search(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)', text)
    if not match:
        raise ValueError('Duration unavailable')
    duration = int(match[1])*3600 + int(match[2])*60 + float(match[3])
    if abs(duration-expected) > 1/FPS+.01:
        raise ValueError(f'Duration {duration}, expected {expected}')
    if f'{W}x{H}' not in vl or f'{FPS} fps' not in vl or 'h264' not in vl.lower():
        raise ValueError(vl)
    if 'aac' not in al.lower() or '48000 Hz' not in al or 'stereo' not in al:
        raise ValueError(f'Audio missing or incorrect: {al}')
    print(f'Duration {duration:.2f}s; {vl}; {al}')

    print('Decoding complete video and audio...', flush=True)
    progress = ff('-v', 'error', '-progress', 'pipe:1', '-nostats', '-i', video,
                  '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-').stdout.decode()
    counts = re.findall(r'^frame=(\d+)$', progress, re.MULTILINE)
    if not counts or int(counts[-1]) != sum(s.frames for s in SCENES):
        raise ValueError(f'Wrong decoded frame count: {counts[-1:]}; expected {sum(s.frames for s in SCENES)}')
    print(f'  {counts[-1]} frames decoded; no errors.')
    loudness = ff('-hide_banner', '-nostats', '-i', video, '-vn', '-af',
                  'ebur128=peak=true:framelog=verbose', '-f', 'null', '-').stderr.decode('utf8', 'replace')
    peaks = re.findall(r'Peak:\s*(-?\d+(?:\.\d+)?)\s+dBFS', loudness)
    if not peaks:
        raise ValueError('Could not measure audio true peak')
    peak = float(peaks[-1])
    if peak > -1:
        raise ValueError(f'Insufficient audio true-peak headroom: {peak} dBFS')
    print(f'  True peak: {peak:.1f} dBFS (oversampled).')

    measured = find_accents()
    if any(abs(t-marker) > .006 for (t, _, _), marker in zip(measured, MUSIC_ACCENTS)):
        raise ValueError('Music transient/grid analysis differs from the edit markers')
    print(f'Music markers rechecked: {sum(detected for _, _, detected in measured)} transient matches and '
          f'{sum(not detected for _, _, detected in measured)} grid estimate; '
          f'maximum frame quantization error {max(abs(frame/FPS-(t-MUSIC_START))*1000 for (t,_,_),frame in zip(measured,ACCENT_FRAMES)):.1f} ms.')
    print('Checking encoded audio against source:')
    verify_audio_alignment(video)
    print('Checking encoded transitions:')
    verify_transitions_and_contact_sheet(video)
    print('All automated checks passed. Review the visual sheets and listen to the export separately.')


if __name__ == '__main__':
    main()
