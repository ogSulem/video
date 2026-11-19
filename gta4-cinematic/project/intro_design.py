"""Spartak art direction: one animated, masked cutout per photograph.

The environment plates are separate people-free imagery. The foreground comes
only from the corresponding Spartak photo; faces are never generated or warped.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont
from motion_art import (AMBER, FPS, H, PAPER, W, base_layer, cutout,
                        foreground_position, preview)

BASE = Path(__file__).resolve().parents[1]

# Source track time. The 4.840 s attack lands at 3.500 s of the finished video.
MUSIC_START = 1.3400
MUSIC_ACCENTS = (
    4.8400, 6.6788, 8.4932, 10.3320, 12.1463, 15.7995, 19.4528,
    23.1059, 26.7591, 30.4123, 34.0654, 37.7185, 41.3717, 45.0252,
    48.6781, 52.3312, 55.9844, 59.6376, 63.2910, 66.9441, 70.5973,
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


# One title card and each of the twenty original Spartak photographs exactly
# once. Per-shot framing retains facial details, groups and significant props.
SCENES = [
    Scene('opening', None, 'harbor_blue_hour', 'right', SCENE_DURATIONS[0]),
    Scene('nightcap', 'IMG_6847', 'rain_street', 'left', SCENE_DURATIONS[1], .88, 1230, 'cut', bleed='left', shift_x=80),
    Scene('bench', 'IMG_6515', 'subway_platform', 'left', SCENE_DURATIONS[2], .86, 1230, 'cut'),
    Scene('park', 'IMG_20200819_205213_Original', 'diner_night', 'left', SCENE_DURATIONS[3], .92, 1200, 'cut'),
    Scene('jacket', 'IMG_6090', 'industrial_dawn', 'right', SCENE_DURATIONS[4], .88, 1220, 'cut'),
    Scene('arrival', 'IMG_6782', 'rooftop_twilight', 'right', SCENE_DURATIONS[5], .94, 1220, 'cut', bleed='right', shift_x=-200),
    Scene('work', 'IMG_7373', 'industrial_dawn', 'left', SCENE_DURATIONS[6], .92, 1150, 'cut'),
    Scene('street', 'IMG_20191118_130227_Original', 'underpass_amber', 'right', SCENE_DURATIONS[7], 1.0, 910, 'cut', grounded=True),
    Scene('drive', 'IMG_6871', 'garage_rednight', 'left', SCENE_DURATIONS[8], .73, 1250, 'cut', bleed='left'),
    Scene('night', 'IMG_7149', 'rain_street', 'right', SCENE_DURATIONS[9], .83, 1200, 'cut'),
    Scene('party', 'IMG_20210101_003521_Original', 'diner_night', 'left', SCENE_DURATIONS[10], .76, 1210, 'cut'),
    Scene('bond', 'IMG_6919', 'subway_platform', 'right', SCENE_DURATIONS[11], .97, 1210, 'cut', max_width=1630),
    Scene('loyalty', 'IMG_6864', 'garage_rednight', 'right', SCENE_DURATIONS[12], .86, 1640, 'cut', bleed='right', max_width=2000),
    Scene('together', 'IMG_6923', 'rain_street', 'right', SCENE_DURATIONS[13], .96, 1210, 'cut', max_width=1630),
    Scene('rules', 'IMG_6853', 'subway_platform', 'left', SCENE_DURATIONS[14], .86, 1210, 'cut'),
    Scene('crew', 'IMG_6854', 'diner_night', 'right', SCENE_DURATIONS[15], .82, 1500, 'cut', bleed='right', max_width=1900),
    Scene('escape', 'IMG_6868', 'rooftop_twilight', 'left', SCENE_DURATIONS[16], .92, 1250, 'cut', bleed='left', max_width=1500, shift_x=160),
    Scene('freedom', 'IMG_6859', 'rain_street', 'right', SCENE_DURATIONS[17], 1.0, 910, 'cut', grounded=True),
    Scene('longnight', 'IMG_6851', 'subway_platform', 'left', SCENE_DURATIONS[18], 1.0, 910, 'cut', grounded=True, bleed='left', max_width=1550),
    Scene('smoke', 'IMG_6759', 'industrial_dawn', 'right', SCENE_DURATIONS[19], .78, 1210, 'cut'),
    Scene('portrait', 'IMG_6779', 'diner_night', 'left', SCENE_DURATIONS[20], .90, 1220, 'cut'),
]


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BASE/'assets'/'fonts'/name), size)


def title_layer(scene: Scene) -> Image.Image | None:
    if scene.key != 'opening':
        return None
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    d.text((150, 265), 'Spartak', font=font('Anton-Regular.ttf', 270),
           fill=(*PAPER, 255), stroke_width=4, stroke_fill=(0, 0, 0, 175))
    d.rectangle((157, 650, 450, 654), fill=(*AMBER, 235))
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--examples', action='store_true')
    args = parser.parse_args()
    out = BASE.parent/'.qc'/'spartak_motion_art'; out.mkdir(parents=True, exist_ok=True)
    scenes = SCENES[:7]+SCENES[9::2] if args.examples else SCENES
    thumbs = []
    for scene in scenes:
        i = SCENES.index(scene); bg, fg, title = build_scene(scene, i, out)
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
