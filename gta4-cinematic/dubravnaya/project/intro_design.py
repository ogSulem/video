"""Art direction for the separate Dubravnaya photo intro.

The earlier edit supplies the non-photographic city plates and font. Only
images in this version's own originals/ and processed/ folders supply people.
Challenging poses/props use intact photographic panels instead of cutouts.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from photos import BASE, REPO, SHARED

W, H, FPS = 1920, 1080, 24
PAPER = (237, 232, 218)
AMBER = (201, 157, 107)

# Same track and opening as the Spartak version: the first photo cuts at 3.5 s
# on the 4.840 s source transient. Four half phrases precede full phrases.
MUSIC_START = 1.3400
MUSIC_ACCENTS = (
    4.8400, 6.6788, 8.4932, 10.3320, 12.1463, 15.7995, 19.4528,
    23.1059, 26.7591, 30.4123, 34.0654, 37.7185, 41.3717, 45.0252,
    48.6781, 52.3312, 55.9844, 59.6376,
)
ACCENT_FRAMES = tuple(round((t - MUSIC_START) * FPS) for t in MUSIC_ACCENTS)
SCENE_DURATIONS = tuple(b - a for a, b in zip((0,) + ACCENT_FRAMES, ACCENT_FRAMES))


@dataclass(frozen=True)
class Scene:
    key: str
    photo: str | None
    plate: str
    side: str
    frames: int
    crop: float = .78          # upper fraction of the cutout, not a face warp
    scale: int = 1210          # height of cutout after preserving aspect ratio
    split: str = 'fade'        # incoming transition
    mode: str = 'cutout'       # cutout or intact panel
    panel_width: int = 1050
    panel_center: tuple[float, float] = (.5, .5)


# Every supplied photo appears exactly once, in attachment order. Framing of
# the panels is individually chosen around the subjects, hands and context.
SCENES = [
    Scene('opening', None, 'harbor_blue_hour', 'right', SCENE_DURATIONS[0]),
    Scene('rest', 'IMG_6976', 'diner_night', 'right', SCENE_DURATIONS[1], split='cut', mode='panel', panel_width=1120, panel_center=(.5, .39)),
    Scene('kitchen', 'IMG_6757', 'subway_platform', 'left', SCENE_DURATIONS[2], .78, split='fade'),
    Scene('redlight', 'IMG_6751', 'rain_street', 'right', SCENE_DURATIONS[3], .65, split='slideleft'),
    Scene('window', '3a003eeb6f62ae091f04215208f19bec', 'industrial_dawn', 'left', SCENE_DURATIONS[4], split='fade', mode='panel', panel_width=1050, panel_center=(.5, .45)),
    Scene('streetduo', 'IMG_6747', 'rain_street', 'right', SCENE_DURATIONS[5], .84, split='slideright'),
    Scene('beanie', 'IMG_6701', 'subway_platform', 'left', SCENE_DURATIONS[6], .96, scale=1100, split='fade'),
    Scene('rooftop', 'IMG_6657', 'harbor_blue_hour', 'right', SCENE_DURATIONS[7], .83, split='slideleft'),
    Scene('call', 'IMG_6659', 'diner_night', 'left', SCENE_DURATIONS[8], split='fade', mode='panel', panel_width=1040, panel_center=(.5, .47)),
    Scene('view', 'IMG_6645', 'harbor_blue_hour', 'right', SCENE_DURATIONS[9], split='slideright', mode='panel', panel_width=1100, panel_center=(.5, .60)),
    Scene('armchair', 'IMG_6639', 'diner_night', 'left', SCENE_DURATIONS[10], split='fade', mode='panel', panel_width=1080, panel_center=(.5, .60)),
    Scene('arms', 'IMG_6636', 'industrial_dawn', 'right', SCENE_DURATIONS[11], split='slideleft', mode='panel', panel_width=1030, panel_center=(.5, .48)),
    Scene('alley', 'IMG_6633', 'subway_platform', 'left', SCENE_DURATIONS[12], split='fade', mode='panel', panel_width=1000, panel_center=(.5, .33)),
    Scene('friends_roof', 'IMG_6612', 'harbor_blue_hour', 'right', SCENE_DURATIONS[13], split='slideright', mode='panel', panel_width=1000, panel_center=(.5, .65)),
    Scene('block', 'IMG_6606', 'industrial_dawn', 'left', SCENE_DURATIONS[14], split='fade', mode='panel', panel_width=1010, panel_center=(.5, .32)),
    Scene('sunset_duo', 'IMG_6584', 'rain_street', 'right', SCENE_DURATIONS[15], .96, scale=1100, split='slideleft'),
    Scene('gesture', 'IMG_6223', 'diner_night', 'left', SCENE_DURATIONS[16], split='fade', mode='panel', panel_width=850, panel_center=(.5, .56)),
    Scene('together', 'IMG_1881', 'subway_platform', 'right', SCENE_DURATIONS[17], .98, scale=1060, split='slideright'),
]


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(SHARED / 'assets' / 'fonts' / name), size)


def image_fill(im: Image.Image, size: tuple[int, int], center=(.5, .5)) -> Image.Image:
    return ImageOps.fit(im, size, method=Image.Resampling.LANCZOS, centering=center)


def load_plate(name: str) -> Image.Image:
    with Image.open(SHARED / 'assets' / 'plates' / f'{name}.jpg') as source:
        im = image_fill(source.convert('RGB'), (W, H))
    im = ImageEnhance.Color(im).enhance(.78)
    im = ImageEnhance.Brightness(im).enhance(.72)
    return im.filter(ImageFilter.GaussianBlur(.6))


def add_grain(im: Image.Image, seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    arr = np.asarray(im).astype(np.int16)
    noise = rng.normal(0, 2.2, (H, W, 1)).astype(np.int16)
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype('uint8'))


def base_layer(scene: Scene, index: int) -> Image.Image:
    plate = load_plate(scene.plate).convert('RGBA')
    shade = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(shade)
    d.rectangle((0, 0, W, H), fill=(5, 13, 16, 38))
    d.rectangle((0, H-190, W, H), fill=(3, 8, 9, 55))
    plate = Image.alpha_composite(plate, shade)
    if scene.photo:
        with Image.open(BASE / 'processed' / f'{scene.photo}_gta4.jpg') as source:
            # Complex poses get a quiet city inset, while cutouts get the same
            # photograph as a full-height counter-panel, as in the prior edit.
            inset_source = load_plate(scene.plate) if scene.mode == 'panel' else source.convert('RGB')
            inset = image_fill(inset_source, (840, H))
        inset = ImageEnhance.Color(inset).enhance(.55)
        inset = ImageEnhance.Brightness(inset).enhance(.64).convert('RGBA')
        if scene.side == 'right':
            origin = (0, 0)
            poly = [(0, 0), (810, 0), (744, H), (0, H)]
            border = [(810, -10), (831, -10), (765, H+10), (744, H+10)]
            line = (819, 0, 753, H)
        else:
            origin = (W-840, 0)
            poly = [(W-810, 0), (W, 0), (W, H), (W-744, H)]
            border = [(W-831, -10), (W-810, -10), (W-744, H+10), (W-765, H+10)]
            line = (W-819, 0, W-753, H)
        layer = Image.new('RGBA', (W, H)); layer.paste(inset, origin)
        stencil = Image.new('L', (W, H)); ImageDraw.Draw(stencil).polygon(poly, fill=255)
        layer.putalpha(stencil); plate = Image.alpha_composite(plate, layer)
        graphic = Image.new('RGBA', (W, H)); gd = ImageDraw.Draw(graphic)
        gd.polygon(border, fill=(5, 9, 10, 255))
        gd.line(line, fill=(*AMBER, 150), width=3)
        plate = Image.alpha_composite(plate, graphic)
    else:
        # Slightly wider title shadow than Spartak to hold the longer word.
        mask = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(mask)
        d.polygon([(0, 0), (W*.75, 0), (W*.55, H), (0, H)], fill=(4, 11, 14, 120))
        d.line((W*.75, 0, W*.55, H), fill=(8, 12, 12, 180), width=12)
        plate = Image.alpha_composite(plate, mask)
    return add_grain(plate.convert('RGB'), index+903)


def photo_panel(scene: Scene) -> Image.Image:
    """A lightly angled photo panel, keeping complex poses photographic."""
    with Image.open(BASE / 'processed' / f'{scene.photo}_gta4.jpg') as source:
        photo = image_fill(source.convert('RGB'), (scene.panel_width, H), scene.panel_center).convert('RGBA')
    x = 0 if scene.side == 'left' else W-scene.panel_width
    layer = Image.new('RGBA', (W, H)); layer.paste(photo, (x, 0))
    stencil = Image.new('L', (W, H)); sd = ImageDraw.Draw(stencil)
    # Only a shallow bevel is clipped at the inner edge, avoiding unnecessary
    # cuts to hands and faces near the photograph's edges.
    edge = 36
    if scene.side == 'left':
        polygon = [(0, 0), (scene.panel_width-edge, 0), (scene.panel_width, H), (0, H)]
        border = [(scene.panel_width-edge-3, 0), (scene.panel_width-edge+22, 0),
                  (scene.panel_width+22, H), (scene.panel_width-3, H)]
    else:
        polygon = [(W-scene.panel_width+edge, 0), (W, 0), (W, H), (W-scene.panel_width, H)]
        border = [(W-scene.panel_width+edge-22, 0), (W-scene.panel_width+edge+3, 0),
                  (W-scene.panel_width+3, H), (W-scene.panel_width-22, H)]
    sd.polygon(polygon, fill=255); layer.putalpha(stencil)
    ink = Image.new('RGBA', (W, H)); ImageDraw.Draw(ink).polygon(border, fill=(5, 9, 10, 255))
    return Image.alpha_composite(ink, layer)


def person_cutout(scene: Scene) -> Image.Image:
    with Image.open(BASE / 'processed' / f'{scene.photo}_gta4.jpg') as source:
        full = source.convert('RGB')
    with Image.open(BASE / 'assets' / 'intro_masks' / f'{scene.photo}.png') as source:
        small = source.convert('L')
    hard = small.point(lambda p: 255 if p > 85 else 0)
    bounds = hard.getbbox()
    if bounds is None:
        raise ValueError(f'Empty foreground mask: {scene.photo}')
    x0, y0, x1, y1 = bounds
    y1 = min(small.height, y0 + max(1, round((y1-y0) * scene.crop)))
    pad = max(3, int(small.width * .008))
    box = (max(0, x0-pad), max(0, y0-pad), min(small.width, x1+pad), min(small.height, y1+pad))
    sx, sy = full.width/small.width, full.height/small.height
    full_box = tuple(round(v * (sx if i % 2 == 0 else sy)) for i, v in enumerate(box))
    image, alpha = full.crop(full_box), small.crop(box)
    h = scene.scale; w = round(image.width * h / image.height)
    if w > 1410:
        h = round(h * 1410 / w); w = 1410
    image = image.resize((w, h), Image.Resampling.LANCZOS)
    alpha = alpha.resize((w, h), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(.7))
    rgba = image.convert('RGBA'); rgba.putalpha(alpha)
    arr = np.asarray(alpha)
    outer = cv2.dilate(arr, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    inner = cv2.dilate(arr, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    pad = 24
    layer = Image.new('RGBA', (w+pad*2, h+pad*2))
    dark = Image.new('RGBA', (w, h), (5, 9, 10, 255)); dark.putalpha(Image.fromarray(outer))
    light = Image.new('RGBA', (w, h), (*PAPER, 255)); light.putalpha(Image.fromarray(inner))
    layer.alpha_composite(dark, (pad, pad)); layer.alpha_composite(light, (pad, pad)); layer.alpha_composite(rgba, (pad, pad))
    x = max(500, min(W-layer.width+12, 940)) if scene.side == 'right' else max(-15, min(180, 810-layer.width))
    y = max(25, 1090-layer.height)
    canvas = Image.new('RGBA', (W, H)); canvas.alpha_composite(layer, (x, y))
    return canvas


def title_layer(scene: Scene) -> Image.Image | None:
    if scene.key != 'opening':
        return None
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    d.text((150, 280), 'Dubravnaya', font=font('Anton-Regular.ttf', 230),
           fill=(*PAPER, 255), stroke_width=4, stroke_fill=(0, 0, 0, 175))
    d.rectangle((157, 635, 450, 639), fill=(*AMBER, 235))
    return im


def build_scene(scene: Scene, index: int, folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    bg = folder / f'{scene.key}_bg.jpg'
    fg = folder / f'{scene.key}_fg.png'
    title = folder / f'{scene.key}_type.png'
    base_layer(scene, index).save(bg, quality=94, subsampling=0, optimize=True, progressive=True)
    if scene.photo:
        (photo_panel(scene) if scene.mode == 'panel' else person_cutout(scene)).save(fg, optimize=True)
    typography = title_layer(scene)
    if typography:
        typography.save(title, optimize=True)
    return bg, (fg if scene.photo else None), (title if typography else None)


def main():
    out = REPO / '.qc' / 'dubravnaya' / 'design'
    out.mkdir(parents=True, exist_ok=True)
    thumbs = []
    for i, scene in enumerate(SCENES):
        bg, fg, title = build_scene(scene, i, out)
        canvas = Image.open(bg).convert('RGBA')
        if fg:
            with Image.open(fg) as im:
                canvas.alpha_composite(im)
        if title:
            with Image.open(title) as im:
                canvas.alpha_composite(im)
        canvas.convert('RGB').resize((960, 540)).save(out / f'{scene.key}_preview.jpg', quality=91)
        thumbs.append((scene.key, canvas.convert('RGB').resize((480, 270))))
        print(scene.key, flush=True)
    rows = math.ceil(len(thumbs)/3)
    sheet = Image.new('RGB', (1440, rows*294), (12, 15, 16)); d = ImageDraw.Draw(sheet)
    for i, (name, image) in enumerate(thumbs):
        x = (i % 3)*480; y = (i // 3)*294
        sheet.paste(image, (x, y)); d.text((x+5, y+273), name, fill='white')
    sheet.save(out / 'overview.jpg', quality=90)
    print(out / 'overview.jpg')


if __name__ == '__main__':
    main()
