"""End-card typography and the deliberate brand reveal.

Copy is the owner-approved set, verbatim, typeset in post (never generated):

    РЕАБИЛИТАЦИОННЫЙ ЦЕНТР АЛТАЙ
    Твой сезон продолжается.
    altaysportreab.ru

The mark is a decorative mountain-and-trail line drawing in the visual language
of the approved Scene 10 plate. It is **not** an official logo and is never
presented as one; no logo file was supplied with the project.

Type is rendered once per element into an RGBA layer, then animated in the
timeline with alpha, rise and a short defocus-to-sharp -- a reveal, not a
slideshow title.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BRAND_NAME = "РЕАБИЛИТАЦИОННЫЙ ЦЕНТР АЛТАЙ"
TAGLINE = "Твой сезон продолжается."
WEBSITE = "altaysportreab.ru"

FONT_CANDIDATES = {
    "serif": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/TTF/DejaVuSerif.ttf",
        "/usr/share/fonts/dejavu/DejaVuSerif.ttf",
    ],
    "serif-bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf",
    ],
    "sans": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ],
}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES[kind]:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    raise FileNotFoundError(
        f"no Cyrillic-capable font found for '{kind}'. Install DejaVu fonts "
        "(package fonts-dejavu-core) before rendering the end card."
    )


# --------------------------------------------------------------------------
# tracked text
# --------------------------------------------------------------------------
def tracked_text(text: str, fnt: ImageFont.FreeTypeFont, tracking: float,
                 fill=(255, 255, 255, 255), pad: int = 24) -> Image.Image:
    """Draw ``text`` with extra letter spacing (tracking in pixels)."""
    widths = []
    for ch in text:
        box = fnt.getbbox(ch)
        widths.append(fnt.getlength(ch))
    total = sum(widths) + tracking * max(0, len(text) - 1)
    ascent, descent = fnt.getmetrics()
    img = Image.new("RGBA", (max(1, int(total) + pad * 2), ascent + descent + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    x = float(pad)
    for ch, w in zip(text, widths):
        draw.text((x, pad), ch, font=fnt, fill=fill)
        x += w + tracking
    return img


def _centre(piece: Image.Image, width: int, y: float) -> tuple[int, int]:
    return int(round((width - piece.width) / 2)), int(round(y - piece.height / 2))


def mountain_mark(height: int = 150, colour=(240, 232, 218, 235),
                  accent=(226, 122, 60, 240)) -> Image.Image:
    """Decorative line mark: two peaks, a trail, a small accent.

    Drawn, not generated. Not a logo -- see the module docstring.
    """
    s = height / 150.0
    w = int(268 * s)
    h = int(150 * s)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lw = max(2, int(round(2 * s)))

    def P(x, y):
        return (x * s, y * s)

    # back peak
    d.line([P(58, 108), P(112, 22), P(150, 74)], fill=colour, width=lw, joint="curve")
    # front peak
    d.line([P(96, 118), P(160, 26), P(214, 106)], fill=colour, width=lw, joint="curve")
    # base line, kept open on the right like a trail leaving the frame
    d.line([P(20, 122), P(104, 122)], fill=colour, width=lw)
    d.line([P(150, 122), P(252, 122)], fill=colour, width=lw)
    # trail: a soft S from the saddle down to the base
    trail = [P(112, 78), P(126, 92), P(140, 100), P(150, 112), P(148, 122)]
    d.line(trail, fill=colour, width=lw, joint="curve")
    # accent: a small plus in the open sky right of the front peak, the only
    # warm note on the card
    cx, cy, r = 231 * s, 62 * s, 8 * s
    d.line([(cx - r, cy), (cx + r, cy)], fill=accent, width=lw)
    d.line([(cx, cy - r), (cx, cy + r)], fill=accent, width=lw)
    return img


# --------------------------------------------------------------------------
# card layers
# --------------------------------------------------------------------------
@dataclass
class CardLayer:
    """One animated element of the end card."""

    image: Image.Image
    x: int
    y: int
    start: float       # seconds into the card
    duration: float
    rise: float = 10.0       # pixels of upward travel while fading in
    defocus: float = 3.0     # initial gaussian radius, sharpened to 0


def build_end_card(width: int, height: int, scale: float = 1.0) -> tuple[np.ndarray, list[CardLayer]]:
    """Return (background RGB, layers). Layers are composited with alpha."""
    # background: deep charcoal with a soft warm centre, matching Scene 10
    bg = np.zeros((height, width, 3), np.float32)
    ys = np.linspace(-1.0, 1.0, height, dtype=np.float32)[:, None]
    xs = np.linspace(-1.0, 1.0, width, dtype=np.float32)[None, :]
    r = np.sqrt((xs * 0.75) ** 2 + (ys * 0.95) ** 2)
    glow = np.clip(1.0 - r / 1.15, 0.0, 1.0) ** 2.2
    base = np.array([0.055, 0.060, 0.070], np.float32)
    centre = np.array([0.115, 0.118, 0.128], np.float32)
    bg = base + (centre - base) * glow[..., None]
    # a whisper of warm reflected light from the bottom, as if the valley were
    # still just off-frame
    warm = (np.clip((ys + 0.2), 0.0, 1.0) ** 2 * 0.018)[..., None]
    bg += warm * np.array([1.0, 0.72, 0.45], np.float32)
    rng = np.random.default_rng(11)
    bg += rng.normal(0, 0.0035, (height, width, 1)).astype(np.float32)
    bg = np.clip(bg * 255.0, 0, 255).astype(np.uint8)

    u = scale
    layers: list[CardLayer] = []

    mark = mountain_mark(int(132 * u))
    mx, my = _centre(mark, width, height * 0.295)
    layers.append(CardLayer(mark, mx, my, 0.10, 1.30, rise=8 * u, defocus=2.4))

    name = tracked_text(BRAND_NAME, font("serif", int(round(53 * u))), tracking=9.5 * u,
                        fill=(247, 240, 227, 255))
    nx, ny = _centre(name, width, height * 0.505)
    layers.append(CardLayer(name, nx, ny, 0.55, 1.45, rise=12 * u, defocus=3.2))

    # hairline rule, drawn as a layer so it can grow
    rule_w = int(round(210 * u))
    rule = Image.new("RGBA", (rule_w, 3), (0, 0, 0, 0))
    ImageDraw.Draw(rule).rectangle([0, 0, rule_w - 1, 1], fill=(214, 200, 178, 150))
    rx, ry = _centre(rule, width, height * 0.585)
    layers.append(CardLayer(rule, rx, ry, 1.15, 1.05, rise=0, defocus=0))

    tag = tracked_text(TAGLINE, font("serif", int(round(35 * u))), tracking=3.2 * u,
                       fill=(226, 216, 200, 255))
    tx, ty = _centre(tag, width, height * 0.665)
    layers.append(CardLayer(tag, tx, ty, 1.60, 1.30, rise=9 * u, defocus=2.2))

    url = tracked_text(WEBSITE, font("sans", int(round(23 * u))), tracking=3.6 * u,
                       fill=(186, 176, 162, 255))
    ux, uy = _centre(url, width, height * 0.745)
    layers.append(CardLayer(url, ux, uy, 2.35, 1.10, rise=6 * u, defocus=1.6))

    return bg, layers


def composite_layers(base: np.ndarray, layers: list[CardLayer], t: float) -> np.ndarray:
    """Composite every layer at card time ``t`` with its own eased reveal."""
    out = Image.fromarray(base).convert("RGBA")
    for layer in layers:
        if t < layer.start:
            continue
        p = float(np.clip((t - layer.start) / max(layer.duration, 1e-6), 0.0, 1.0))
        eased = 1.0 - (1.0 - p) ** 3
        alpha = eased
        img = layer.image
        if layer.defocus > 0.0 and p < 1.0:
            img = img.filter(ImageFilter.GaussianBlur(layer.defocus * (1.0 - eased)))
        if alpha < 0.999:
            arr = np.array(img, dtype=np.float32)
            arr[..., 3] *= alpha
            img = Image.fromarray(arr.astype(np.uint8))
        dy = int(round(-layer.rise * (1.0 - eased)))
        out.alpha_composite(img, (layer.x, layer.y + dy))
    return np.array(out.convert("RGB"))
