"""Optionally regenerate the foreground masks used by the Dubravnaya edit.

Requires mediapipe==0.10.21 as well as the regular project dependencies. The
renderer itself uses the stored masks and does not need MediaPipe. Complex
poses and important props use intact photo panels rather than unreliable masks.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageFilter, ImageOps
from photos import BASE

MASK_NAMES = (
    'IMG_6757', 'IMG_6751', 'IMG_6747', 'IMG_6701', 'IMG_6657', 'IMG_6584', 'IMG_1881',
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE / 'assets' / 'intro_masks')
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    with mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0) as model:
        for name in MASK_NAMES:
            with Image.open(BASE / 'originals' / f'{name}.jpeg') as source:
                im = ImageOps.exif_transpose(source).convert('RGB')
            im.thumbnail((768, 1024), Image.Resampling.LANCZOS)
            probability = model.process(np.asarray(im)).segmentation_mask
            alpha = (np.clip((probability - .26) / .50, 0, 1) * 255).astype(np.uint8)
            # Keep substantial components (including both people in pairs),
            # but remove tiny detached background fragments.
            count, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 75).astype(np.uint8), 8)
            if count > 1:
                largest = max(stats[1:, cv2.CC_STAT_AREA])
                keep = np.zeros_like(alpha)
                for k in range(1, count):
                    if stats[k, cv2.CC_STAT_AREA] >= largest * .012:
                        keep[labels == k] = 255
                alpha = np.minimum(alpha, cv2.dilate(keep, np.ones((3, 3), np.uint8)))

            # Small hand-reviewed exclusions in 768×1024 thumbnail coordinates.
            # Only background fragments are removed; these do not repaint the
            # actual people or their faces. Other difficult photos stay panels.
            h, w = alpha.shape
            if name == 'IMG_6751':
                # A strip of wall was mistaken for hair at the left of the head.
                ys = [274, 284, 294, 304, 314, 324, 334, 344, 354, 364, 369, 373]
                xs = [250, 239, 231, 228, 225, 223, 222, 219, 217, 213, 204, 185]
                for yy in range(round(274*h/1024), min(round(373*h/1024), h)):
                    cutoff = round(np.interp(yy*1024/h, ys, xs)*w/768)
                    alpha[yy, :cutoff] = 0
            elif name == 'IMG_6657':
                # Remove a sliver of balcony attached to the bent sleeve.
                ys = [510, 525, 540, 555, 570, 585, 600, 630, 660, 675]
                xs = [405, 401, 397, 388, 376, 365, 357, 350, 346, 346]
                for yy in range(round(510*h/1024), min(round(675*h/1024), h)):
                    cutoff = round(np.interp(yy*1024/h, ys, xs)*w/768)
                    alpha[yy, cutoff:] = 0
            elif name == 'IMG_1881':
                # A bright rectangle of room background between the sleeve and
                # lower edge otherwise appears as a floating outlined block.
                points = [(722, 825), (767, 825), (767, 908), (730, 908), (722, 895)]
                points = np.array([[(x*w/768, y*h/1024) for x, y in points]], dtype=np.int32)
                cv2.fillPoly(alpha, points, 0)
            Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(.65)).save(out / f'{name}.png', optimize=True)
            print(f'mask: {name}', flush=True)


if __name__ == '__main__':
    main()
