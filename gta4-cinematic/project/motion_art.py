"""Shared art direction for the two photo-only, moving-cutout intros.

Only the environment plates and fonts are shared. Every character layer is
read from the invoking version's own processed photograph and reviewed mask.
No photograph is ever used as a background, inset, or second subject layer.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

SHARED = Path(__file__).resolve().parents[1]
W, H, FPS = 1920, 1080, 24
PAPER = (237, 232, 218)
AMBER = (201, 157, 107)

# Every inset is a different people-free city plate, not the source portrait.
# Swapping the two produces the angled, graphic split-screen rhythm.
INSET = {
    'harbor_blue_hour': 'rooftop_twilight',
    'rooftop_twilight': 'harbor_blue_hour',
    'rain_street': 'underpass_amber',
    'underpass_amber': 'rain_street',
    'industrial_dawn': 'subway_platform',
    'subway_platform': 'industrial_dawn',
    'diner_night': 'garage_rednight',
    'garage_rednight': 'diner_night',
}


def load_plate(name: str) -> Image.Image:
    with Image.open(SHARED / 'assets' / 'plates' / f'{name}.jpg') as source:
        im = ImageOps.fit(source.convert('RGB'), (W, H), method=Image.Resampling.LANCZOS)
    im = ImageEnhance.Color(im).enhance(.83)
    return ImageEnhance.Brightness(im).enhance(.88).filter(ImageFilter.GaussianBlur(.45))


def base_layer(scene, index: int) -> Image.Image:
    """Two generated urban locations and ink geometry; never a user photo."""
    plate = load_plate(scene.plate).convert('RGBA')
    shade = Image.new('RGBA', (W, H))
    d = ImageDraw.Draw(shade)
    d.rectangle((0, 0, W, H), fill=(5, 12, 16, 28))
    d.rectangle((0, H-130, W, H), fill=(3, 7, 9, 32))
    plate = Image.alpha_composite(plate, shade)

    if scene.photo:
        # The secondary plate is slightly subdued, leaving the portrait as the
        # brightest point while keeping enough texture for the moving parallax.
        inset = ImageOps.fit(load_plate(INSET[scene.plate]), (750, H),
                             method=Image.Resampling.LANCZOS, centering=(.5, .5))
        inset = ImageEnhance.Color(inset).enhance(.76)
        inset = ImageEnhance.Brightness(inset).enhance(.78).convert('RGBA')
        if scene.side == 'right':
            origin = (0, 0)
            shape = [(0, 0), (710, 0), (650, H), (0, H)]
            border = [(709, 0), (732, 0), (672, H), (649, H)]
            rule = (729, 0, 669, H)
        else:
            origin = (W-750, 0)
            shape = [(W-710, 0), (W, 0), (W, H), (W-650, H)]
            border = [(W-732, 0), (W-709, 0), (W-649, H), (W-672, H)]
            rule = (W-729, 0, W-669, H)
        panel = Image.new('RGBA', (W, H)); panel.paste(inset, origin)
        stencil = Image.new('L', (W, H)); ImageDraw.Draw(stencil).polygon(shape, fill=255)
        panel.putalpha(stencil); plate = Image.alpha_composite(plate, panel)
        ink = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(ink)
        d.polygon(border, fill=(4, 7, 8, 255))
        d.line(rule, fill=(*AMBER, 160), width=3)
        plate = Image.alpha_composite(plate, ink)
    else:
        ink = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(ink)
        d.polygon([(0, 0), (W*.75, 0), (W*.55, H), (0, H)], fill=(4, 10, 13, 115))
        d.line((W*.75, 0, W*.55, H), fill=(6, 9, 10, 230), width=15)
        d.line((W*.75+13, 0, W*.55+13, H), fill=(*AMBER, 140), width=3)
        plate = Image.alpha_composite(plate, ink)

    # Static subtle monochrome texture; the camera move makes it feel alive.
    rng = np.random.default_rng(index + 1903)
    arr = np.asarray(plate.convert('RGB')).astype(np.int16)
    noise = rng.normal(0, 1.6, (H, W, 1)).astype(np.int16)
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype('uint8'))


def cutout(scene, base: Path) -> Image.Image:
    """Return one tightly cropped, outlined RGBA layer for this photograph."""
    if not scene.photo:
        raise ValueError('The title has no foreground photograph')
    with Image.open(base / 'processed' / f'{scene.photo}_gta4.jpg') as source:
        full = source.convert('RGB')
    with Image.open(base / 'assets' / 'motion_masks' / f'{scene.photo}.png') as source:
        small = source.convert('L')
    bounds = small.point(lambda p: 255 if p > 85 else 0).getbbox()
    if bounds is None:
        raise ValueError(f'Empty foreground mask: {scene.photo}')
    x0, y0, x1, y1 = bounds
    # All cropping is performed on the mask and photograph together. We crop
    # below the faces, never synthesize or change a person's expression.
    y1 = min(small.height, y0 + max(1, round((y1-y0)*scene.crop)))
    pad = max(3, round(small.width*.006))
    box = (max(0, x0-pad), max(0, y0-pad), min(small.width, x1+pad), min(small.height, y1+pad))
    sx, sy = full.width/small.width, full.height/small.height
    full_box = tuple(round(v*(sx if i % 2 == 0 else sy)) for i, v in enumerate(box))
    image, alpha = full.crop(full_box), small.crop(box)
    if scene.photo == '3a003eeb6f62ae091f04215208f19bec':
        # This portrait was strongly backlit; a small, pixel-preserving contrast
        # adjustment helps reveal its existing face without inventing detail.
        image = ImageEnhance.Contrast(image).enhance(1.23)
        image = ImageEnhance.Brightness(image).enhance(1.07)
        image = ImageEnhance.Color(image).enhance(1.10)
    h = scene.scale
    w = round(image.width*h/image.height)
    if w > scene.max_width:
        h = round(h*scene.max_width/w)
        w = scene.max_width
    image = image.resize((w, h), Image.Resampling.LANCZOS)
    alpha = alpha.resize((w, h), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(.45))

    # Dilate on a padded canvas, so neither outline nor shadow is clipped at
    # the source rectangle. The dark ink and fine warm edge echo GTA IV art.
    pad = 22
    alpha_canvas = Image.new('L', (w+2*pad, h+2*pad)); alpha_canvas.paste(alpha, (pad, pad))
    a = np.asarray(alpha_canvas)
    outer = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (29, 29)))
    inner = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    canvas = Image.new('RGBA', alpha_canvas.size)
    dark = Image.new('RGBA', canvas.size, (4, 7, 8, 255)); dark.putalpha(Image.fromarray(outer))
    fine = Image.new('RGBA', canvas.size, (*PAPER, 255)); fine.putalpha(Image.fromarray(inner))
    person = image.convert('RGBA'); person.putalpha(alpha)
    canvas.alpha_composite(dark); canvas.alpha_composite(fine); canvas.alpha_composite(person, (pad, pad))
    return canvas


def foreground_position(scene, size: tuple[int, int]) -> tuple[int, int]:
    """Center pose on the chosen side, allowing cropped source edges to bleed."""
    width, height = size
    center = 590 if scene.side == 'left' else 1330
    if width <= W-180:
        x = max(90, min(W-width-90, round(center-width/2)))
    else:
        x = round((W-width)/2)
    if scene.bleed == 'left':
        x = -100
    elif scene.bleed == 'right':
        x = W-width+100
    elif scene.bleed not in ('', None):
        raise ValueError(f'Unknown bleed placement: {scene.bleed}')
    # Complete figures can stand at the frame foot. Cropped torsos extend
    # below it, avoiding a detached, horizontal cut line.
    y = H-height-42 if scene.grounded else max(75, H-height+95)
    return round(x+scene.shift_x), round(y+scene.shift_y)


def preview(scene, bg: Path, fg: Path | None, title: Path | None) -> Image.Image:
    with Image.open(bg) as source:
        canvas = source.convert('RGBA')
    if fg is not None:
        with Image.open(fg) as source:
            figure = source.convert('RGBA')
        canvas.alpha_composite(figure, foreground_position(scene, figure.size))
    if title is not None:
        with Image.open(title) as source:
            canvas.alpha_composite(source.convert('RGBA'))
    return canvas.convert('RGB')
