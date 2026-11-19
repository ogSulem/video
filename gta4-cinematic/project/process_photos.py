"""
GTA IV Cinematic Photo Processor
Applies per-photo color grading in Liberty City aesthetic.
- Cold blue-green shadows, muted orange highlights
- Desaturation, contrast S-curve, crushed blacks
- Vignette + film grain
- Outputs: processed/ (full-res) + assets/cinematic_16x9/ (1920x1080 crops for video)
"""
import argparse
import os, random
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

# Resolve paths relative to this file so the scripts also work outside the repo root.
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "originals"
DST_FULL = BASE / "processed"
DST_169 = BASE / "assets" / "cinematic_16x9"
os.makedirs(DST_FULL, exist_ok=True)
os.makedirs(DST_169, exist_ok=True)

# Per-photo grade presets: (saturation, contrast, brightness, color_temp_shift, vignette_strength, grain)
# color_temp_shift: -1 cool .. +1 warm (applied as RGB gain)
PRESETS = {
    "IMG_20191118_130227_Original.jpeg": dict(sat=0.70, con=1.12, bri=0.91, temp=-0.08, vig=0.32, grain=14, note="Day wet street - overcast desat, cool shadows"),
    "IMG_20210101_003521_Original.jpeg": dict(sat=0.68, con=1.18, bri=0.86, temp=-0.05, vig=0.38, grain=16, note="Interior party mirror - warm flash tamed"),
    "IMG_6759.jpeg": dict(sat=0.70, con=1.15, bri=0.90, temp=-0.10, vig=0.42, grain=18, note="Night BBQ smoke - deep blacks, fire glow muted"),
    "IMG_6779.jpeg": dict(sat=0.85, con=1.10, bri=1.00, temp=-0.06, vig=0.35, grain=12, note="Mirror portrait brick - controlled, cinematic"),
    "IMG_6782.jpeg": dict(sat=0.88, con=1.08, bri=1.00, temp=-0.04, vig=0.28, grain=10, note="Bridge dusk - wide establishing, blue hour"),
    "IMG_6851.jpeg": dict(sat=0.72, con=1.20, bri=0.95, temp=-0.12, vig=0.48, grain=20, note="Bench night exhaustion - darkest, most depressive"),
    "IMG_6853.jpeg": dict(sat=0.80, con=1.16, bri=0.99, temp=-0.09, vig=0.40, grain=16, note="99 crosswalk solo - street icon, flash night"),
    "IMG_6854.jpeg": dict(sat=0.80, con=1.16, bri=0.99, temp=-0.09, vig=0.40, grain=16, note="99 duo night - brotherhood"),
    "IMG_6859.jpeg": dict(sat=0.75, con=1.18, bri=0.98, temp=-0.10, vig=0.44, grain=18, note="Shirtless night park - raw, sodium streetlight"),
    "IMG_6864.jpeg": dict(sat=0.82, con=1.14, bri=1.00, temp=-0.07, vig=0.36, grain=14, note="Night street duo - flash, urban"),
    "IMG_6868.jpeg": dict(sat=0.69, con=1.10, bri=0.91, temp=-0.03, vig=0.30, grain=10, note="Lake BBQ day - escape, softer grade"),
    "IMG_6871.jpeg": dict(sat=0.78, con=1.14, bri=0.97, temp=-0.08, vig=0.40, grain=16, note="Car interior - moody, dashboard glow"),
    "IMG_6919.jpeg": dict(sat=0.66, con=1.15, bri=0.90, temp=-0.09, vig=0.38, grain=15, note="Night trees duo hoodie"),
    "IMG_6923.jpeg": dict(sat=0.66, con=1.15, bri=0.90, temp=-0.09, vig=0.38, grain=15, note="Night trees duo bottle"),
    "IMG_7149.jpeg": dict(sat=0.82, con=1.14, bri=0.99, temp=-0.08, vig=0.38, grain=15, note="Lada night city - neon, phone glow"),
    "IMG_7373.jpeg": dict(sat=0.73, con=1.12, bri=0.90, temp=-0.05, vig=0.30, grain=12, note="Construction day - gritty overcast"),
}

def grade_image(im, p):
    # im: PIL RGB
    # 1. Enhance via PIL
    im = ImageEnhance.Color(im).enhance(p["sat"])
    im = ImageEnhance.Contrast(im).enhance(p["con"])
    im = ImageEnhance.Brightness(im).enhance(p["bri"])
    # 2. Numpy color grade: S-curve + temp shift + shadow tint
    arr = np.asarray(im).astype(np.float32) / 255.0
    # S-curve: x -> x + a*x*(1-x)*(x-0.5)  (a=0.35)
    a = 0.35
    arr = arr + a * arr * (1-arr) * (arr - 0.5) * 2
    # Temp shift: cool = boost B,G slightly, reduce R
    t = p["temp"]  # negative = cool
    arr[...,0] = np.clip(arr[...,0] * (1 + t*0.6), 0, 1)  # R
    arr[...,1] = np.clip(arr[...,1] * (1 - t*0.2), 0, 1)  # G slight opposite
    arr[...,2] = np.clip(arr[...,2] * (1 - t*0.8), 0, 1)  # B
    # Shadow tint blue-green: add to dark areas
    lum = arr.mean(axis=2, keepdims=True)
    shadow_mask = np.clip(1 - lum*2.2, 0, 1)  # 1 in shadows
    arr[...,0] = np.clip(arr[...,0] - 0.03*shadow_mask[...,0], 0, 1)
    arr[...,1] = np.clip(arr[...,1] + 0.015*shadow_mask[...,0], 0, 1)
    arr[...,2] = np.clip(arr[...,2] + 0.035*shadow_mask[...,0], 0, 1)
    # Crush blacks slightly
    arr = np.clip((arr - 0.02) / 0.98, 0, 1)
    arr = (arr*255).astype(np.uint8)
    im = Image.fromarray(arr)
    # 3. Vignette
    w,h = im.size
    y,x = np.ogrid[:h,:w]
    cx,cy = w/2, h/2
    dist = np.sqrt(((x-cx)/(w*0.62))**2 + ((y-cy)/(h*0.62))**2)
    vig = 1 - p["vig"] * np.clip(dist-0.55, 0, 1)**1.6
    arr = np.asarray(im).astype(np.float32) * vig[...,None]
    im = Image.fromarray(np.clip(arr,0,255).astype(np.uint8))
    # 4. Fine monochrome grain. Keep skin texture instead of burying it in noise.
    # The preset is an intensity dial, not a standard deviation in 8-bit units.
    g = p["grain"] * 0.20
    noise = np.random.normal(0, g, (h,w,1)).astype(np.float32)
    arr = np.asarray(im).astype(np.float32) + noise
    im = Image.fromarray(np.clip(arr,0,255).astype(np.uint8))
    # 5. Restrained local contrast; no artificial skin smoothing.
    im = im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=35, threshold=3))
    return im

# Manually reviewed vertical framing in the EXIF-corrected photo (0 = top).
# Portraits differ: a uniform upper-third crop would cut off several faces.
CROP_CENTERS = {
    "IMG_20191118_130227_Original.jpeg": 0.21,
    "IMG_20210101_003521_Original.jpeg": 0.32,
    "IMG_6759.jpeg": 0.32,
    "IMG_6779.jpeg": 0.43,
    "IMG_6782.jpeg": 0.48,
    "IMG_6851.jpeg": 0.50,
    "IMG_6853.jpeg": 0.21,
    "IMG_6854.jpeg": 0.41,
    "IMG_6859.jpeg": 0.45,
    "IMG_6864.jpeg": 0.40,
    "IMG_6868.jpeg": 0.38,
    "IMG_6871.jpeg": 0.37,
    "IMG_6919.jpeg": 0.60,
    "IMG_6923.jpeg": 0.60,
    "IMG_7149.jpeg": 0.23,
    "IMG_7373.jpeg": 0.39,
}

def crop_16x9(im, center_y=0.5, target=(1920,1080)):
    w,h = im.size
    target_ratio = target[0]/target[1]
    cur_ratio = w/h
    if cur_ratio > target_ratio:
        # too wide -> crop width
        new_w = int(h*target_ratio)
        x0 = (w-new_w)//2
        box = (x0, 0, x0+new_w, h)
    else:
        # Crop vertically around the manually chosen focal point, not a template.
        new_h = int(w/target_ratio)
        cy = int(h * center_y)
        y0 = max(0, min(cy - new_h//2, h-new_h))
        box = (0, y0, w, y0+new_h)
    cropped = im.crop(box)
    cropped = cropped.resize(target, Image.LANCZOS)
    return cropped

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lossless", action="store_true", help="also save full-resolution PNGs (requires substantial disk space)")
    args = parser.parse_args()
    random.seed(42); np.random.seed(42)
    files = sorted(os.listdir(SRC))
    for f in files:
        if not f.lower().endswith(('.jpg','.jpeg','.png')): continue
        src = os.path.join(SRC,f)
        im = Image.open(src)
        im = ImageOps.exif_transpose(im).convert("RGB")
        p = PRESETS.get(f, dict(sat=0.82, con=1.12, bri=0.99, temp=-0.07, vig=0.36, grain=14, note="default"))
        graded = grade_image(im, p)
        base = os.path.splitext(f)[0]
        out_full = os.path.join(DST_FULL, f"{base}_gta4.jpg")
        graded.save(out_full, quality=95, subsampling=0, optimize=True, progressive=True)
        if args.lossless:
            # Added PNGs preserve the processed RGB pixels without a further
            # lossy encode. Original photos were already JPEGs.
            graded.save(os.path.join(DST_FULL, f"{base}_gta4.png"), compress_level=6)
        c169 = crop_16x9(graded, CROP_CENTERS.get(f, 0.5))
        out_169 = os.path.join(DST_169, f"{base}_16x9.jpg")
        c169.save(out_169, quality=92, subsampling=0, optimize=True, progressive=True)
        print(f"{f} -> {out_full} ({graded.size}) + 16x9 {c169.size} | {p['note']}")
    print("Done.")

if __name__=="__main__":
    main()
