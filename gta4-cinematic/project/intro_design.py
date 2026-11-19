"""Art direction and deterministic layered artwork for the photo-based intro.

Foreground people are cut from the graded original photographs with stored
masks; no face is generated, exchanged, smoothed, or geometrically changed.
City plates are separate generated environmental assets with no people.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps

BASE = Path(__file__).resolve().parents[1]
W, H, FPS = 1920, 1080, 24
PAPER = (237, 232, 218)
AMBER = (201, 157, 107)

# Phrase accents in the supplied, slowed track. Most were matched against the
# same percussive transient; 45.0252 is the corresponding rhythmic-grid point
# in a quieter/changed bar. The last marker is the end of the music excerpt.
# At 24 fps, each accent can be represented only to the nearest 1/24 second.
MUSIC_ACCENTS = (
    4.8400, 8.4932, 12.1464, 15.7995, 19.4528, 23.1060,
    26.7591, 30.4123, 34.0654, 37.7186, 41.3717, 45.0252,
    48.6781, 52.3312, 55.9845, 59.6376, 63.2910,
)
ACCENT_FRAMES = tuple(round(t * FPS) for t in MUSIC_ACCENTS)
SCENE_DURATIONS = tuple(b - a for a, b in zip((0,) + ACCENT_FRAMES, ACCENT_FRAMES))
# Complex group/seat/arm poses remain inside intact angled photo panels rather
# than using an imperfect mask that could make limbs or bodies look broken.
PHOTO_PANELS = {"drive", "party", "escape", "longnight"}


@dataclass(frozen=True)
class Scene:
    key: str  # internal identifier only; never rendered as text
    photo: str | None
    plate: str
    side: str
    frames: int  # time between the centres of adjacent transitions
    crop: float = .72  # fraction of foreground height, from the top
    scale: int = 1210
    split: str = "fade"


# One title card and all sixteen photographs. The last image fades out; there
# is no separate GTA title card. Scene durations are quantized independently,
# avoiding cumulative drift from rounding a constant number of frames per beat.
SCENES = [
    Scene("opening", None, "harbor_blue_hour", "right", SCENE_DURATIONS[0]),
    Scene("arrival", "IMG_6782", "harbor_blue_hour", "right", SCENE_DURATIONS[1], .78, split="slideleft"),
    Scene("work", "IMG_7373", "industrial_dawn", "left", SCENE_DURATIONS[2], .67, split="fade"),
    Scene("street", "IMG_20191118_130227_Original", "diner_night", "right", SCENE_DURATIONS[3], .66, split="slideright"),
    Scene("drive", "IMG_6871", "rain_street", "left", SCENE_DURATIONS[4], .80, split="fade"),
    Scene("night", "IMG_7149", "rain_street", "right", SCENE_DURATIONS[5], .57, split="slideleft"),
    Scene("party", "IMG_20210101_003521_Original", "diner_night", "left", SCENE_DURATIONS[6], .65, split="fade"),
    Scene("bond", "IMG_6919", "subway_platform", "right", SCENE_DURATIONS[7], .95, split="slideleft"),
    Scene("loyalty", "IMG_6864", "diner_night", "left", SCENE_DURATIONS[8], .80, split="slideright"),
    Scene("together", "IMG_6923", "rain_street", "right", SCENE_DURATIONS[9], .94, split="fade"),
    Scene("rules", "IMG_6853", "subway_platform", "left", SCENE_DURATIONS[10], .65, split="slideleft"),
    Scene("crew", "IMG_6854", "diner_night", "right", SCENE_DURATIONS[11], .70, split="fade"),
    Scene("escape", "IMG_6868", "harbor_blue_hour", "left", SCENE_DURATIONS[12], .85, split="slideright"),
    Scene("freedom", "IMG_6859", "rain_street", "right", SCENE_DURATIONS[13], .72, split="fade"),
    Scene("longnight", "IMG_6851", "subway_platform", "left", SCENE_DURATIONS[14], .95, split="slideleft"),
    Scene("smoke", "IMG_6759", "industrial_dawn", "right", SCENE_DURATIONS[15], .69, split="fade"),
    Scene("portrait", "IMG_6779", "diner_night", "left", SCENE_DURATIONS[16], .70, split="slideright"),
]


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BASE / "assets" / "fonts" / name), size)


def image_fill(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(im, size, method=Image.Resampling.LANCZOS, centering=(.5, .5))



def load_plate(name: str) -> Image.Image:
    im = Image.open(BASE / "assets" / "plates" / f"{name}.jpg").convert("RGB")
    im = image_fill(im, (W, H))
    im = ImageEnhance.Color(im).enhance(.78)
    im = ImageEnhance.Brightness(im).enhance(.72)
    return im.filter(ImageFilter.GaussianBlur(.6))


def add_grain(im: Image.Image, seed: int) -> Image.Image:
    # Very subtle deterministic mono texture, stronger in shadow than faces.
    rng = np.random.default_rng(seed)
    arr = np.asarray(im).astype(np.int16)
    noise = rng.normal(0, 2.2, (H, W, 1)).astype(np.int16)
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype("uint8"))


def base_layer(scene: Scene, index: int) -> Image.Image:
    plate = load_plate(scene.plate).convert("RGBA")
    shade = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(shade)
    d.rectangle((0, 0, W, H), fill=(5, 13, 16, 38))
    d.rectangle((0, H - 190, W, H), fill=(3, 8, 9, 55))
    plate = Image.alpha_composite(plate, shade)
    if scene.photo:
        # The full-height inset replaces the old dark box for numbered titles.
        # Use the original portrait framing, so the bottom remains photographic.
        source = Image.open(BASE / "processed" / f"{scene.photo}_gta4.jpg").convert("RGB")
        # For complex poses the main panel retains the whole photo, so its side
        # panel shows the city instead of duplicating the people.
        inset_source = load_plate(scene.plate) if scene.key in PHOTO_PANELS else source
        inset = image_fill(inset_source, (840, H))
        inset = ImageEnhance.Color(inset).enhance(.55)
        inset = ImageEnhance.Brightness(inset).enhance(.64).convert("RGBA")
        if scene.side == "right":
            origin = (0, 0)
            poly = [(0, 0), (810, 0), (744, H), (0, H)]
            border = [(810, -10), (831, -10), (765, H+10), (744, H+10)]
            line = (819, 0, 753, H)
        else:
            origin = (W - 840, 0)
            poly = [(W - 810, 0), (W, 0), (W, H), (W - 744, H)]
            border = [(W - 831, -10), (W - 810, -10), (W - 744, H+10), (W - 765, H+10)]
            line = (W - 819, 0, W - 753, H)
        tmp = Image.new("RGBA", (W, H));tmp.paste(inset, origin)
        stencil = Image.new("L", (W, H));ImageDraw.Draw(stencil).polygon(poly, fill=255)
        tmp.putalpha(stencil);plate = Image.alpha_composite(plate, tmp)
        graphics = Image.new("RGBA", (W, H));gd = ImageDraw.Draw(graphics)
        gd.polygon(border, fill=(5, 9, 10, 255))
        # A tiny warm edge provides the poster-ink separation without neon.
        gd.line(line, fill=(*AMBER, 150), width=3)
        plate = Image.alpha_composite(plate, graphics)
    else:
        mask = Image.new("RGBA", (W,H));d=ImageDraw.Draw(mask)
        d.polygon([(0, 0), (W*.66, 0), (W*.48, H), (0,H)], fill=(4, 11, 14, 115))
        d.line((W*.66, 0, W*.48, H), fill=(8, 12, 12, 180), width=12)
        plate = Image.alpha_composite(plate, mask)
    return add_grain(plate.convert("RGB"), index + 903)


def cutout(scene: Scene) -> Image.Image:
    assert scene.photo
    if scene.key in PHOTO_PANELS:
        # Preserve difficult overlapping figures/props as an intact graphic
        # photo panel rather than cutting off limbs or inventing missing pixels.
        image = Image.open(BASE / "assets" / "cinematic_16x9" / f"{scene.photo}_16x9.jpg").convert("RGB")
        panel_w = 1280
        center = {"escape": (.05, .5), "party": (.33, .5)}.get(scene.key, (.5, .5))
        photo = ImageOps.fit(image, (panel_w, H), method=Image.Resampling.LANCZOS, centering=center).convert("RGBA")
        layer = Image.new("RGBA", (W, H))
        x = 0 if scene.side == "left" else W-panel_w
        layer.paste(photo, (x, 0))
        mask = Image.new("L", (W,H));md=ImageDraw.Draw(mask)
        if scene.side == "left":
            polygon=[(0,0),(panel_w-80,0),(panel_w,H),(0,H)]
            border=[(panel_w-82,0),(panel_w-56,0),(panel_w+24,H),(panel_w-2,H)]
        else:
            polygon=[(W-panel_w+80,0),(W,0),(W,H),(W-panel_w,H)]
            border=[(W-panel_w+56,0),(W-panel_w+82,0),(W-panel_w+2,H),(W-panel_w-24,H)]
        md.polygon(polygon,fill=255);layer.putalpha(mask)
        ink=Image.new("RGBA",(W,H));d=ImageDraw.Draw(ink);d.polygon(border,fill=(5,9,10,255))
        layer=Image.alpha_composite(ink,layer)
        return layer
    full = Image.open(BASE / "processed" / f"{scene.photo}_gta4.jpg").convert("RGB")
    small = Image.open(BASE / "assets" / "intro_masks" / f"{scene.photo}.png").convert("L")
    # bbox threshold ignores almost-transparent ghost pixels, preventing
    # scattered background fragments from changing composition or size.
    hard = small.point(lambda p: 255 if p > 85 else 0)
    bounds = hard.getbbox()
    if bounds is None:
        raise ValueError(f"Empty foreground mask: {scene.photo}")
    x0,y0,x1,y1 = bounds
    y1 = min(small.height, y0 + max(1, round((y1-y0) * scene.crop)))
    pad = max(3, int(small.width * .008))
    box = (max(0,x0-pad), max(0,y0-pad), min(small.width,x1+pad), min(small.height,y1+pad))
    sx, sy = full.width/small.width, full.height/small.height
    full_box = tuple(round(v * (sx if i%2==0 else sy)) for i,v in enumerate(box))
    image = full.crop(full_box)
    alpha = small.crop(box)
    h = scene.scale
    w = round(image.width * h / image.height)
    if w > 1410:
        h = round(h * 1410 / w); w = 1410
    image = image.resize((w,h), Image.Resampling.LANCZOS)
    alpha = alpha.resize((w,h), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(.7))
    rgba = image.convert("RGBA");rgba.putalpha(alpha)

    # 2 strokes: near-black graphic keyline, then a thin warm paper outline.
    a = np.asarray(alpha)
    outer = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25,25)))
    inner = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9,9)))
    padding=24
    layer=Image.new("RGBA",(w+padding*2,h+padding*2))
    dark=Image.new("RGBA",(w,h),(5,9,10,255));dark.putalpha(Image.fromarray(outer))
    light=Image.new("RGBA",(w,h),(*PAPER,255));light.putalpha(Image.fromarray(inner))
    layer.alpha_composite(dark,(padding,padding));layer.alpha_composite(light,(padding,padding));layer.alpha_composite(rgba,(padding,padding))
    # Place the people within frame without stretching proportions. The lower
    # edge extends off-screen so a cut torso does not appear to float.
    if scene.side == "right":
        x = min(W - layer.width + 12, 940)
        x = max(500, x)
    else:
        x = max(-15, min(180, 810-layer.width))
    y = max(25, 1090-layer.height)
    canvas = Image.new("RGBA",(W,H))
    canvas.alpha_composite(layer,(x,y))
    return canvas


def title_layer(scene: Scene) -> Image.Image | None:
    # The user's single requested title is visible in frame zero. No titles,
    # numbers, city labels or captions are drawn on the photo scenes.
    if scene.key != "opening":
        return None
    im = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(im)
    d.text((150, 265), "Spartak", font=font("Anton-Regular.ttf", 270),
           fill=(*PAPER, 255), stroke_width=4, stroke_fill=(0, 0, 0, 175))
    d.rectangle((157, 650, 450, 654), fill=(*AMBER, 235))
    return im

def build_scene(scene: Scene, index: int, folder: Path):
    folder.mkdir(parents=True,exist_ok=True)
    bg=folder/f"{scene.key}_bg.jpg"; fg=folder/f"{scene.key}_fg.png"; title=folder/f"{scene.key}_type.png"
    base_layer(scene,index).save(bg,quality=94,subsampling=0,optimize=True,progressive=True)
    if scene.photo:
        cutout(scene).save(fg,optimize=True)
    typography = title_layer(scene)
    if typography:
        typography.save(title,optimize=True)
    return bg,(fg if scene.photo else None),(title if typography else None)


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--examples",action="store_true");args=p.parse_args()
    out=BASE.parent/".qc"/"intro_design";out.mkdir(parents=True,exist_ok=True)
    scenes=[SCENES[i] for i in (0,1,2,4,5,6,7,8,9,10,11,12,13,14,15,16)] if args.examples else SCENES
    thumbs=[]
    for scene in scenes:
        i=SCENES.index(scene);bg,fg,title=build_scene(scene,i,out)
        canvas=Image.open(bg).convert("RGBA")
        if fg:canvas.alpha_composite(Image.open(fg))
        if title:canvas.alpha_composite(Image.open(title))
        canvas.convert("RGB").resize((640,360)).save(out/f"{scene.key}_preview.jpg",quality=90)
        thumbs.append((scene.key,canvas.convert("RGB").resize((480,270))))
        print(scene.key,flush=True)
    rows=math.ceil(len(thumbs)/3);sheet=Image.new("RGB",(1440,rows*294),(12,15,16));d=ImageDraw.Draw(sheet)
    for i,(name,image) in enumerate(thumbs):
        x=(i%3)*480;y=(i//3)*294;sheet.paste(image,(x,y));d.text((x+5,y+273),name,fill="white")
    sheet.save(out/"overview.jpg",quality=90)
    print(out/"overview.jpg")


if __name__ == "__main__":
    main()
