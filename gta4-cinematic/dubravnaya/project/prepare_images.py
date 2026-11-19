"""Make render-sized graded copies of the Dubravnaya photographs.

Original JPEGs are never modified. The same grade function as the Spartak
edit is used, with independent filename-based grain and restrained individual
exposure adjustments. The longest edge is capped at 2560 px: the renderer
outputs 1080p, while the untouched originals retain the source resolution.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps
from photos import BASE, SHARED, PHOTO_NAMES

# Reuse the prior edit's colour treatment without changing its source or data.
sys.path.insert(0, str(SHARED / 'project'))
from process_photos import grade_image  # noqa: E402

MAX_EDGE = 2560
DEFAULT = dict(sat=.82, con=1.10, bri=1.00, temp=-.06, vig=.27, grain=11)
# Shadow-lift values below 1 brighten existing pixels, particularly in the
# backlit window and sunset pictures. No image content is generated or replaced.
ADJUSTMENTS = {
    'IMG_6976': dict(sat=.82, con=1.08, bri=1.01, temp=-.04, vig=.23),
    'IMG_6757': dict(sat=.78, con=1.09, bri=1.03, temp=-.05, vig=.25),
    'IMG_6751': dict(sat=.83, con=1.08, bri=1.02, temp=-.035, vig=.22),
    '3a003eeb6f62ae091f04215208f19bec': dict(sat=.82, con=1.06, bri=1.02, temp=-.03, vig=.20, shadow_gamma=.72, local_contrast=1.7),
    'IMG_6747': dict(sat=.82, con=1.10, bri=1.03, temp=-.04, vig=.25),
    'IMG_6701': dict(sat=.82, con=1.09, bri=1.00, temp=-.04, vig=.25),
    'IMG_6657': dict(sat=.79, con=1.08, bri=1.03, temp=-.06, vig=.24, shadow_gamma=.88),
    'IMG_6659': dict(sat=.80, con=1.09, bri=1.01, temp=-.04, vig=.24),
    'IMG_6645': dict(sat=.77, con=1.08, bri=1.00, temp=-.05, vig=.22),
    'IMG_6639': dict(sat=.79, con=1.09, bri=1.00, temp=-.04, vig=.24),
    'IMG_6636': dict(sat=.77, con=1.10, bri=1.01, temp=-.06, vig=.24),
    'IMG_6633': dict(sat=.76, con=1.08, bri=1.04, temp=-.06, vig=.22),
    'IMG_6612': dict(sat=.80, con=1.08, bri=1.00, temp=-.06, vig=.22),
    'IMG_6606': dict(sat=.80, con=1.09, bri=1.00, temp=-.05, vig=.22),
    'IMG_6584': dict(sat=.82, con=1.08, bri=1.02, temp=-.05, vig=.22, shadow_gamma=.82),
    'IMG_6223': dict(sat=.80, con=1.08, bri=.98, temp=-.035, vig=.23),
    'IMG_1881': dict(sat=.83, con=1.08, bri=1.00, temp=-.035, vig=.23),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE / 'processed')
    parser.add_argument('--only', choices=PHOTO_NAMES, help='process one photo instead of all 17')
    args = parser.parse_args()
    folder = args.output
    folder.mkdir(parents=True, exist_ok=True)
    actual = {p.stem for p in (BASE / 'originals').glob('*.jpeg')}
    if actual != set(PHOTO_NAMES):
        raise ValueError('The originals folder must contain exactly the 17 Dubravnaya photos')
    for name in (PHOTO_NAMES if args.only is None else (args.only,)):
        path = BASE / 'originals' / f'{name}.jpeg'
        with Image.open(path) as source:
            im = ImageOps.exif_transpose(source).convert('RGB')
        source_size = im.size
        im.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
        settings = DEFAULT | ADJUSTMENTS.get(name, {})
        gamma = settings.pop('shadow_gamma', 1.)
        local_contrast = settings.pop('local_contrast', 0.)
        if gamma != 1.:
            lut = [round(255 * (v / 255) ** gamma) for v in range(256)]
            im = im.point(lut * 3)
        if local_contrast:
            # Recover some shadow detail from the strongly backlit window shot.
            # CLAHE changes luminance only; it does not invent facial features.
            lab = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2LAB)
            lab[:, :, 0] = cv2.createCLAHE(clipLimit=local_contrast, tileGridSize=(8, 8)).apply(lab[:, :, 0])
            im = Image.fromarray(cv2.cvtColor(lab, cv2.COLOR_LAB2RGB))
        np.random.seed(int.from_bytes(hashlib.sha256(name.encode('utf-8')).digest()[:4], 'big'))
        graded = grade_image(im, settings)
        dest = folder / f'{name}_gta4.jpg'
        graded.save(dest, quality=93, subsampling=0, optimize=True, progressive=True)
        print(f'{path.name}: {source_size} -> {graded.size} -> {dest.name}', flush=True)


if __name__ == '__main__':
    main()
