"""Inspect foreground motion in encoded frames, not only in the edit settings.

Tracks corners inside each reviewed foreground matte at three points per scene.
The scene's background is deliberately excluded from the measurement. The
contact sheets are also intended for manual review of framing and masks.
"""
from __future__ import annotations

from pathlib import Path
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw
from motion_art import FPS, H, W, cutout
from motion_render import motion_spec

WIDTH, HEIGHT = 320, 180


def _decode(ff: str, video: Path, frames: list[int]):
    ordered = sorted(set(frames))
    select = '+'.join(f'eq(n,{n})' for n in ordered)
    cmd = [ff, '-v', 'error', '-i', str(video), '-an', '-vf',
           f"select='{select}',scale={WIDTH}:{HEIGHT},format=rgb24", '-fps_mode', 'passthrough',
           '-f', 'rawvideo', '-c:v', 'rawvideo', '-threads', '1', '-']
    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    size = WIDTH*HEIGHT*3
    if len(result) != len(ordered)*size:
        raise ValueError(f'Expected {len(ordered)} motion sample frames, got {len(result)//size}')
    images = np.frombuffer(result, np.uint8).reshape(-1, HEIGHT, WIDTH, 3)
    return dict(zip(ordered, images))


def _positioned_mask(alpha: Image.Image, spec: dict, local_frame: int, frames: int):
    p = local_frame/(frames-1)
    zoom = spec['zoom_start']+(spec['zoom_end']-spec['zoom_start'])*p
    sw = max(2, int(spec['width']*zoom/2)*2)
    sh = max(2, int(spec['height']*zoom/2)*2)
    x = spec['x']-(sw-spec['width'])/2+spec['dx']*(p-.5)
    anchor = 1 if spec['grounded'] else .5
    y = spec['y']-(sh-spec['height'])*anchor+spec['dy']*(p-.5)
    m = alpha.resize((max(1, round(sw*WIDTH/W)), max(1, round(sh*HEIGHT/H))), Image.Resampling.LANCZOS)
    canvas = Image.new('L', (WIDTH, HEIGHT))
    canvas.paste(m, (round(x*WIDTH/W), round(y*HEIGHT/H)))
    binary = (np.asarray(canvas) > 245).astype('uint8')*255
    return cv2.erode(binary, np.ones((3, 3), np.uint8))


def _track(a, b, area, expected_dx):
    first = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    second = cv2.cvtColor(b, cv2.COLOR_RGB2GRAY)
    pts = cv2.goodFeaturesToTrack(first, maxCorners=240, qualityLevel=.006,
                                 minDistance=2.5, mask=area, blockSize=5)
    if pts is None or len(pts) < 3:
        return None, 0, 0
    p2, status, err = cv2.calcOpticalFlowPyrLK(first, second, pts, None,
                                               winSize=(25, 25), maxLevel=3,
                                               criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT, 30, .01))
    if p2 is None:
        return None, 0, len(pts)
    pback, back_status, _ = cv2.calcOpticalFlowPyrLK(second, first, p2, None,
                                                     winSize=(25, 25), maxLevel=3)
    if pback is None:
        return None, 0, len(pts)
    delta = (p2-pts).reshape(-1, 2)
    fb = np.linalg.norm((pback-pts).reshape(-1, 2), axis=1)
    good = (status.reshape(-1) != 0) & (back_status.reshape(-1) != 0) & (fb < 1.8) & (err.reshape(-1) < 40)
    # The moving figure's scale changes too. The allowed band covers that zoom
    # at either edge of a wide group while excluding a stationary background.
    tol = max(4.5, abs(expected_dx)*.65)
    good &= np.abs(delta[:, 0]-expected_dx) < tol
    good &= np.abs(delta[:, 1]) < 8
    candidates = delta[good, 0]
    if len(candidates) < 3:
        return None, len(candidates), len(pts)
    return float(np.median(candidates)), len(candidates), len(pts)


def verify_encoded_motion(video: Path, scenes, base: Path, ff: str, hard_cut_before, qc: Path):
    starts, elapsed = [], 0
    for scene in scenes:
        starts.append(elapsed)
        elapsed += scene.frames
    requests = []
    offsets = {}
    for i, scene in enumerate(scenes):
        if not scene.photo:
            continue
        # The last still fades out, so measure before that visual fade.
        fractions = (.15, .38, .60) if i == len(scenes)-1 else (.15, .50, .85)
        times = tuple(max(1, min(scene.frames-2, round(scene.frames*f))) for f in fractions)
        offsets[i] = times
        requests.extend(starts[i]+t for t in times)
    images = _decode(ff, video, requests)
    qc.mkdir(parents=True, exist_ok=True)
    samples = []
    failures = []
    for i, scene in enumerate(scenes):
        if not scene.photo:
            continue
        if not hard_cut_before(i) or scene.split != 'cut':
            raise ValueError(f'Overlapping photo scenes would duplicate subjects: {scene.key}')
        frames = scene.frames
        fg = cutout(scene, base)
        alpha = fg.getchannel('A')
        spec = motion_spec(scene, i, fg.size, frames)
        if abs(spec['dx']) < 100 or abs(spec['zoom_end']-spec['zoom_start']) < .05:
            raise ValueError(f'Insufficient designed continuous motion: {scene.key}')
        o = offsets[i]
        local = o
        samples.append((scene.key, [images[starts[i]+t] for t in o]))
        observed = []
        for j in (0, 1):
            p0, p1 = local[j], local[j+1]
            region = _positioned_mask(alpha, spec, p0, frames)
            expected = spec['dx']*(p1-p0)/(frames-1)*(WIDTH/W)
            median, good, total = _track(images[starts[i]+o[j]], images[starts[i]+o[j+1]], region, expected)
            if median is None or median*expected <= 0:
                failures.append(f'{scene.key} interval {j+1}: {good}/{total} inliers; expected dx {expected:+.1f}px at {WIDTH}w')
                observed.append('?')
            else:
                observed.append(f'{median:+.1f}px ({good}/{total})')
        print(f"  {scene.key:14} subject motion: {'  |  '.join(observed)}", flush=True)
    # Before/middle/end samples from the encoded video; five scenes per sheet.
    for start in range(0, len(samples), 5):
        section = samples[start:start+5]
        sheet = Image.new('RGB', (WIDTH*3, (HEIGHT+24)*len(section)), (9, 12, 14))
        draw = ImageDraw.Draw(sheet)
        for row, (key, frames) in enumerate(section):
            for col, frame in enumerate(frames):
                x, y = col*WIDTH, row*(HEIGHT+24)
                sheet.paste(Image.fromarray(frame), (x, y))
                draw.text((x+5, y+HEIGHT+4), f'{key}  sample {col+1}', fill='white')
        sheet.save(qc/f'motion_{start//5+1:02d}.jpg', quality=92)
    if failures:
        raise ValueError('Unable to track subject motion in encoded frames:\n  '+'\n  '.join(failures))
    print(f'  {len(samples)} photo layers move in both sampled intervals; sheets: {qc}', flush=True)
