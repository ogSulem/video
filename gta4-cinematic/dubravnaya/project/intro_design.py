"""Dubravnaya art direction: one animated, masked cutout per photograph.

Only city plates, fonts and music are shared with Spartak. Character layers
come exclusively from this version's own photographs and reviewed masks.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import sys

from PIL import Image, ImageDraw, ImageFont
from photos import BASE, REPO, SHARED

# Keep the local project ahead of the shared helpers: both projects have their
# own intro_design.py and render_intro.py modules.
sys.path.append(str(SHARED/'project'))
from motion_art import (AMBER, FPS, H, PAPER, W, base_layer, cutout,
                        foreground_position, preview)  # noqa: E402

MUSIC_START = 1.3400
MUSIC_ACCENTS = (
    4.8400, 6.6788, 8.4932, 10.3320, 12.1463, 15.7995, 19.4528,
    23.1059, 26.7591, 30.4123, 34.0654, 37.7185, 41.3717, 45.0252,
    48.6781, 52.3312, 55.9844, 59.6376,
)
ACCENT_FRAMES = tuple(round((t-MUSIC_START)*FPS) for t in MUSIC_ACCENTS)
SCENE_DURATIONS = tuple(b-a for a, b in zip((0,)+ACCENT_FRAMES, ACCENT_FRAMES))


@dataclass(frozen=True)
class Scene:
    key: str
    photo: str | None
    plate: str
    side: str
    frames: int
    crop: float = .86
    scale: int = 1210
    split: str = 'cut'
    grounded: bool = False
    bleed: str = ''
    max_width: int = 1560
    shift_x: int = 0
    shift_y: int = 0


# All seventeen Dubravnaya photographs in attachment order. Every photo has
# exactly one person/people mask, including former panel-only scenes.
SCENES = [
    Scene('opening', None, 'harbor_blue_hour', 'right', SCENE_DURATIONS[0]),
    Scene('rest', 'IMG_6976', 'garage_rednight', 'left', SCENE_DURATIONS[1], .98, 1220, 'cut', bleed='left', shift_x=100),
    Scene('kitchen', 'IMG_6757', 'subway_platform', 'left', SCENE_DURATIONS[2], .86, 1210, 'cut', bleed='left', shift_x=90),
    Scene('redlight', 'IMG_6751', 'garage_rednight', 'right', SCENE_DURATIONS[3], 1.0, 910, 'cut', grounded=True),
    Scene('window', '3a003eeb6f62ae091f04215208f19bec', 'industrial_dawn', 'left', SCENE_DURATIONS[4], .88, 1210, 'cut'),
    Scene('streetduo', 'IMG_6747', 'rain_street', 'right', SCENE_DURATIONS[5], .92, 1300, 'cut', bleed='right', max_width=1650, shift_x=-200),
    Scene('beanie', 'IMG_6701', 'subway_platform', 'left', SCENE_DURATIONS[6], .94, 1260, 'cut', bleed='left', max_width=1600),
    Scene('rooftop', 'IMG_6657', 'rooftop_twilight', 'right', SCENE_DURATIONS[7], .84, 1190, 'cut'),
    Scene('call', 'IMG_6659', 'underpass_amber', 'left', SCENE_DURATIONS[8], .98, 1200, 'cut'),
    Scene('view', 'IMG_6645', 'harbor_blue_hour', 'right', SCENE_DURATIONS[9], 1.0, 1220, 'cut', bleed='right', max_width=1650, shift_x=-100),
    Scene('armchair', 'IMG_6639', 'diner_night', 'left', SCENE_DURATIONS[10], 1.0, 1190, 'cut', bleed='left', max_width=1540),
    Scene('arms', 'IMG_6636', 'underpass_amber', 'right', SCENE_DURATIONS[11], 1.0, 1090, 'cut', max_width=1500),
    Scene('alley', 'IMG_6633', 'subway_platform', 'left', SCENE_DURATIONS[12], 1.0, 910, 'cut', grounded=True),
    Scene('friends_roof', 'IMG_6612', 'rooftop_twilight', 'right', SCENE_DURATIONS[13], 1.0, 910, 'cut', grounded=True),
    Scene('block', 'IMG_6606', 'industrial_dawn', 'left', SCENE_DURATIONS[14], .98, 1190, 'cut', bleed='left', shift_x=100),
    Scene('sunset_duo', 'IMG_6584', 'rain_street', 'right', SCENE_DURATIONS[15], .98, 1240, 'cut', bleed='right', shift_x=-200),
    Scene('gesture', 'IMG_6223', 'diner_night', 'left', SCENE_DURATIONS[16], .98, 1210, 'cut', bleed='left', shift_x=80),
    Scene('together', 'IMG_1881', 'subway_platform', 'right', SCENE_DURATIONS[17], .98, 1430, 'cut', bleed='right', max_width=1800),
]


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(SHARED/'assets'/'fonts'/name), size)


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
    bg = folder/f'{scene.key}_bg.png'; fg = folder/f'{scene.key}_fg.png'; title = folder/f'{scene.key}_type.png'
    # Lossless intermediate avoids adding another JPEG generation before H.264.
    base_layer(scene, index).save(bg, compress_level=3)
    if scene.photo:
        cutout(scene, BASE).save(fg, optimize=True)
    typography = title_layer(scene)
    if typography:
        typography.save(title, optimize=True)
    return bg, (fg if scene.photo else None), (title if typography else None)


def main():
    out = REPO/'.qc'/'dubravnaya_motion_art'; out.mkdir(parents=True, exist_ok=True)
    thumbs = []
    for i, scene in enumerate(SCENES):
        bg, fg, title = build_scene(scene, i, out)
        canvas = preview(scene, bg, fg, title)
        canvas.resize((960, 540), Image.Resampling.LANCZOS).save(out/f'{scene.key}_preview.jpg', quality=91)
        thumbs.append((scene.key, canvas.resize((480, 270), Image.Resampling.LANCZOS)))
        print(scene.key, flush=True)
    sheet = Image.new('RGB', (1440, math.ceil(len(thumbs)/3)*294), (12, 15, 16)); d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(thumbs):
        x, y = (i % 3)*480, (i // 3)*294
        sheet.paste(im, (x, y)); d.text((x+5, y+273), name, fill='white')
    sheet.save(out/'overview.jpg', quality=92)
    print(out/'overview.jpg')


if __name__ == '__main__':
    main()
