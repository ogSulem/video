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
BEAT_FRAMES = 16  # 90 BPM at 24fps
INK = (8, 14, 16)
PAPER = (237, 232, 218)
AMBER = (201, 157, 107)
# Complex group/seat/arm poses remain inside intact angled photo panels rather
# than using an imperfect mask that could make limbs or bodies look broken.
PHOTO_PANELS = {"drive", "party", "escape", "longnight"}


@dataclass(frozen=True)
class Scene:
    key: str
    photo: str | None
    plate: str
    title: str
    sub: str
    side: str
    frames: int
    crop: float = .72  # fraction of foreground height, from the top
    scale: int = 1210
    split: str = "fade"


# The start of every scene lies on the beat: all frame counts are multiples
# of 16. Short dissolves / panel slides begin on those same beats.
SCENES = [
    Scene("opening", None, "harbor_blue_hour", "LIBERTY\nCITY", "EVERY CITY HAS A STORY", "right", 64, split="fade"),
    Scene("arrival", "IMG_6782", "harbor_blue_hour", "THE\nARRIVAL", "A NEW BEGINNING", "right", 96, .78, split="slideleft"),
    Scene("work", "IMG_7373", "industrial_dawn", "HARD\nWORK", "NO EASY WAY OUT", "left", 64, .67, split="fade"),
    Scene("street", "IMG_20191118_130227_Original", "diner_night", "THE\nSTREETS", "ONE DAY AT A TIME", "right", 64, .66, split="slideright"),
    Scene("drive", "IMG_6871", "rain_street", "NO TURNING\nBACK", "THE ROAD AHEAD", "left", 96, .80, split="fade"),
    Scene("night", "IMG_7149", "rain_street", "AFTER\nDARK", "THE CITY NEVER SLEEPS", "right", 96, .57, split="slideleft"),
    Scene("party", "IMG_20210101_003521_Original", "diner_night", "GOOD\nTIMES", "THE ONES WHO STAY", "left", 64, .65, split="fade"),
    Scene("bond", "IMG_6919", "subway_platform", "BROTHER\nHOOD", "THROUGH THE NIGHT", "right", 96, .95, split="slideleft"),
    Scene("interlude", None, "industrial_dawn", "EVERY DREAM\nHAS A PRICE", "LIBERTY CITY // 2008", "left", 64, split="fade"),
    Scene("loyalty", "IMG_6864", "diner_night", "LOYALTY", "STICK TOGETHER", "left", 64, .80, split="slideright"),
    Scene("together", "IMG_6923", "rain_street", "NO\nSHORTCUTS", "THE LONG WAY HOME", "right", 64, .94, split="fade"),
    Scene("rules", "IMG_6853", "subway_platform", "STREET\nRULES", "A DIFFERENT KIND OF FREEDOM", "left", 96, .65, split="slideleft"),
    Scene("crew", "IMG_6854", "diner_night", "THE\nCREW", "NO ONE GOES ALONE", "right", 96, .70, split="fade"),
    Scene("escape", "IMG_6868", "harbor_blue_hour", "A MOMENT\nAWAY", "OUTSIDE THE CITY", "left", 64, .85, split="slideright"),
    Scene("freedom", "IMG_6859", "rain_street", "FREEDOM", "AFTER HOURS", "right", 64, .72, split="fade"),
    Scene("longnight", "IMG_6851", "subway_platform", "THE LONG\nNIGHT", "EVERY STORY LEAVES A MARK", "left", 64, .95, split="slideleft"),
    Scene("smoke", "IMG_6759", "industrial_dawn", "THROUGH\nTHE SMOKE", "THE ONES WE REMEMBER", "right", 96, .69, split="fade"),
    Scene("portrait", "IMG_6779", "diner_night", "ONE LAST\nLOOK", "THE STORY GOES ON", "left", 96, .70, split="slideright"),
    Scene("closing", None, "harbor_blue_hour", "GRAND\nTHEFT\nAUTO", "A CINEMATIC FAN INTRO", "right", 128, split="fade"),
]


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BASE / "assets" / "fonts" / name), size)


def image_fill(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(im, size, method=Image.Resampling.LANCZOS, centering=(.5, .5))


def draw_tracking(draw, xy, text, f, fill, spacing=3):
    x, y = xy
    for c in text:
        draw.text((x, y), c, font=f, fill=fill)
        x += draw.textlength(c, font=f) + spacing


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
        source = Image.open(BASE / "assets" / "cinematic_16x9" / f"{scene.photo}_16x9.jpg").convert("RGB")
        # For complex poses the main panel retains the whole photo, so its side
        # panel shows the city instead of a second, duplicated copy of the people.
        inset_source = load_plate(scene.plate) if scene.key in PHOTO_PANELS else source
        inset = image_fill(inset_source, (790, 700))
        inset = ImageEnhance.Color(inset).enhance(.55)
        inset = ImageEnhance.Brightness(inset).enhance(.60).convert("RGBA")
        if scene.side == "right":
            origin = (0, 0)
            poly = [(0, 0), (810, 0), (744, 710), (0, 710)]
            border = [(814, -10), (838, -10), (767, 723), (742, 723)]
            bottom = [(0, 710), (745, 710), (708, H), (0, H)]
        else:
            origin = (W - 790, 0)
            poly = [(W - 810, 0), (W, 0), (W, 710), (W - 744, 710)]
            border = [(W - 838, -10), (W - 814, -10), (W - 742, 723), (W - 767, 723)]
            bottom = [(W - 745, 710), (W, 710), (W, H), (W - 708, H)]
        tmp = Image.new("RGBA", (W, H));tmp.paste(inset, origin)
        stencil = Image.new("L", (W, H));ImageDraw.Draw(stencil).polygon(poly, fill=255)
        tmp.putalpha(stencil);plate = Image.alpha_composite(plate, tmp)
        graphics = Image.new("RGBA", (W, H));gd = ImageDraw.Draw(graphics)
        gd.polygon(bottom, fill=(6, 13, 15, 225))
        gd.polygon(border, fill=(5, 9, 10, 255))
        gd.line((0, 705, 780, 705) if scene.side == "right" else (W-780, 705, W, 705), fill=(7, 10, 11, 255), width=16)
        # A tiny warm edge provides the poster-ink separation without neon.
        line = (819, 0, 754, 705) if scene.side == "right" else (W - 819, 0, W - 754, 705)
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


def title_layer(scene: Scene, index: int) -> Image.Image:
    im=Image.new("RGBA",(W,H));d=ImageDraw.Draw(im)
    if scene.key == "closing":
        f=font("Anton-Regular.ttf",188)
        for i,line in enumerate(scene.title.split("\n")):
            d.text((155, 140+i*170),line,font=f,fill=(*PAPER,255),stroke_width=4,stroke_fill=(4,7,8,225))
        d.text((760, 285),"IV",font=font("Anton-Regular.ttf",280),fill=(*AMBER,255),stroke_width=4,stroke_fill=(4,7,8,230))
        d.line((165, 790, 1110,790),fill=(*AMBER,210),width=3)
        draw_tracking(d,(165,820),scene.sub,font("IBMPlexMono-Medium.ttf",25),(*PAPER,235),3)
        draw_tracking(d,(165,870),"NOT AN OFFICIAL ROCKSTAR GAMES PRODUCTION",font("IBMPlexMono-Medium.ttf",17),(194,194,186,215),2)
        return im
    if scene.photo is None:
        label_font=font("IBMPlexMono-Medium.ttf",24)
        draw_tracking(d,(155,170),"A FAN-MADE STORY",label_font,(*AMBER,240),4)
        lines=scene.title.split("\n"); fs=164 if scene.key=="opening" else 122
        f=font("Anton-Regular.ttf",fs)
        y=265 if scene.key=="opening" else 320
        for line in lines:
            d.text((150,y),line,font=f,fill=(*PAPER,250),stroke_width=3,stroke_fill=(0,0,0,150)); y += fs*1.08
        d.line((157,y+35,460,y+35),fill=(*AMBER,225),width=4)
        draw_tracking(d,(157,y+68),scene.sub,label_font,(*PAPER,230),3)
        return im

    # A quiet, consistent title block sits over the dark lower corner.
    x = 82 if scene.side == "right" else 1175
    top = 728
    # Keep lettering legible even where a bright jacket crosses the panel.
    d.polygon([(x-24,top-18),(x+650,top-18),(x+625,H),(x-24,H)], fill=(5,12,14,218))
    d.rectangle((x,top,x+52,top+52),fill=(*AMBER,245))
    d.text((x+8,top+5),f"{index:02d}",font=font("IBMPlexMono-Medium.ttf",27),fill=(10,15,15,255))
    draw_tracking(d,(x+71,top+14),"LIBERTY CITY",font("IBMPlexMono-Medium.ttf",22),(*PAPER,220),3)
    lines=scene.title.split("\n")
    available=630
    sz=92 if len(lines)>1 else 106
    f=font("Anton-Regular.ttf",sz)
    while max(d.textbbox((0,0),line,font=f)[2] for line in lines)>available and sz>55:
        sz -= 2;f=font("Anton-Regular.ttf",sz)
    y=top+74
    for line in lines:
        # Anton has a large top bearing: position by its actual ink bounds,
        # so the subtitle never overlaps the final line.
        box=d.textbbox((0,0),line,font=f)
        d.text((x,y-box[1]),line,font=f,fill=(*PAPER,255),stroke_width=3,stroke_fill=(2,5,6,200))
        y+=box[3]-box[1]+10
    draw_tracking(d,(x,y+10),scene.sub,font("IBMPlexMono-Medium.ttf",20),(*AMBER,235),2)
    return im


def build_scene(scene: Scene, index: int, folder: Path):
    folder.mkdir(parents=True,exist_ok=True)
    bg=folder/f"{scene.key}_bg.jpg"; fg=folder/f"{scene.key}_fg.png"; title=folder/f"{scene.key}_type.png"
    base_layer(scene,index).save(bg,quality=94,subsampling=0,optimize=True,progressive=True)
    if scene.photo:
        cutout(scene).save(fg,optimize=True)
    title_layer(scene,index).save(title,optimize=True)
    return bg,(fg if scene.photo else None),title


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--examples",action="store_true");args=p.parse_args()
    out=BASE.parent/".qc"/"intro_design";out.mkdir(parents=True,exist_ok=True)
    scenes=[SCENES[i] for i in (0,1,2,5,6,7,9,11,12,13,15,16,17,18)] if args.examples else SCENES
    thumbs=[]
    for scene in scenes:
        i=SCENES.index(scene);bg,fg,title=build_scene(scene,i,out)
        canvas=Image.open(bg).convert("RGBA")
        if fg:canvas.alpha_composite(Image.open(fg))
        canvas.alpha_composite(Image.open(title));canvas.convert("RGB").resize((640,360)).save(out/f"{scene.key}_preview.jpg",quality=90)
        thumbs.append((scene.key,canvas.convert("RGB").resize((480,270))))
        print(scene.key,flush=True)
    rows=math.ceil(len(thumbs)/3);sheet=Image.new("RGB",(1440,rows*294),(12,15,16));d=ImageDraw.Draw(sheet)
    for i,(name,image) in enumerate(thumbs):
        x=(i%3)*480;y=(i//3)*294;sheet.paste(image,(x,y));d.text((x+5,y+273),name,fill="white")
    sheet.save(out/"overview.jpg",quality=90)
    print(out/"overview.jpg")


if __name__ == "__main__":
    main()
