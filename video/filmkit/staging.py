"""Living stills — 2.5D staging for the approved photographs.

The v2 renderer moved a still by cropping it. That reads as a photograph being
pushed around: there is no depth, no atmosphere, and a person frozen mid-gesture
gives it away in the first second.

This module builds the missing depth from what the frame actually contains:

* a **depth proxy** — ground plane below, wall and glass above, refined from
  luminance so the floor and the far wall separate where they really do;
* a **depth-layered camera**: the near layer travels and scales more than the
  far layer, so the room has real parallax instead of a flat slide;
* a **focus pull**: the far layer is resolved slightly softer and the near
  layer sharpens over the shot, the way a real lens behaves;
* **atmosphere** — falling snow, drifting light, a slow exposure breath.

No cut-out is involved, so there are no matte edges to give the trick away.
The class is deterministic: ``render(t)`` depends only on ``t``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

cv2.setNumThreads(max(1, min(4, cv2.getNumberOfCPUs())))


# --------------------------------------------------------------------------
# easing helpers
# --------------------------------------------------------------------------
def smoothstep(x: float) -> float:
    x = float(np.clip(x, 0.0, 1.0))
    return x * x * (3.0 - 2.0 * x)


def ease_in_out(x: float) -> float:
    x = float(np.clip(x, 0.0, 1.0))
    return 0.5 - 0.5 * np.cos(np.pi * x)


def lerp(a: float, b: float, x: float) -> float:
    return a + (b - a) * x


# --------------------------------------------------------------------------
# depth proxy
# --------------------------------------------------------------------------
def depth_proxy(rgb: np.ndarray, horizon: float = 0.55,
                softness: float = 0.16) -> np.ndarray:
    """A smooth 0..1 depth map: 1 is near (floor), 0 is far (wall, glass, sky).

    The base is a vertical ramp around ``horizon``. It is then nudged by local
    luminance contrast so flat bright glass reads as further away than the
    textured floor in front of it. Everything is blurred heavily, so the map
    can only ever produce a gentle parallax -- never a seam.
    """
    h, w = rgb.shape[:2]
    ys = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    ramp = 1.0 / (1.0 + np.exp(-(ys - horizon) / max(softness, 1e-3)))
    ramp = np.broadcast_to(ramp, (h, w)).astype(np.float32)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    detail = np.abs(cv2.Laplacian(gray, cv2.CV_32F, ksize=3))
    detail = cv2.GaussianBlur(detail, (0, 0), 9.0)
    detail /= max(float(detail.max()), 1e-6)
    depth = np.clip(ramp * (0.75 + 0.5 * detail), 0.0, 1.0)
    depth = cv2.GaussianBlur(depth, (0, 0), max(3.0, min(h, w) * 0.02))
    return np.clip(depth, 0.0, 1.0)


# --------------------------------------------------------------------------
# atmosphere
# --------------------------------------------------------------------------
@dataclass
class SnowField:
    """Deterministic falling snow drawn as soft streaks with parallax depth.

    Flakes are seeded once, then advected with time. Depth controls size,
    speed and brightness, so the field has real layering instead of reading as
    a tiled texture.
    """

    count: int = 110
    speed: float = 150.0
    drift: float = 30.0
    size: float = 2.0
    opacity: float = 0.5
    seed: int = 7
    blur: float = 1.1
    _cache: tuple | None = field(default=None, repr=False)

    def _state(self):
        if self._cache is None:
            rng = np.random.default_rng(self.seed)
            n = self.count
            self._cache = (
                rng.uniform(-0.15, 1.15, n).astype(np.float32),
                rng.uniform(-0.15, 1.15, n).astype(np.float32),
                rng.uniform(0.35, 1.7, n).astype(np.float32),
                rng.uniform(0.5, 1.6, n).astype(np.float32),
                rng.uniform(0, 2 * np.pi, n).astype(np.float32),
                rng.uniform(0.30, 1.0, n).astype(np.float32),
            )
        return self._cache

    def layer(self, t: float, width: int, height: int) -> np.ndarray:
        x0, y0, depth, size_mul, phase, bright = self._state()
        wobble = 0.010 * np.sin(t * 1.4 + phase)
        xs = (x0 + (self.drift * depth) * t / width + wobble) % 1.3 - 0.15
        ys = (y0 + (self.speed * depth) * t / height) % 1.3 - 0.15
        px, py = xs * width, ys * height
        length = (2.5 + self.speed * depth * 0.05) * size_mul
        mask = np.zeros((height, width), np.float32)
        for i in range(len(px)):
            if not (-30 < px[i] < width + 30 and -30 < py[i] < height + 30):
                continue
            thickness = max(1, int(round(self.size * size_mul[i] * 0.65)))
            cv2.line(mask,
                     (int(px[i]), int(py[i])),
                     (int(px[i] - self.drift * 0.03 * depth[i]),
                      int(py[i] + length[i])),
                     float(bright[i]), thickness, cv2.LINE_AA)
        if self.blur > 0:
            mask = cv2.GaussianBlur(mask, (0, 0), self.blur)
        return (mask * self.opacity)[..., None]

    def apply(self, img: np.ndarray, t: float) -> np.ndarray:
        m = self.layer(t, img.shape[1], img.shape[0])
        return img * (1.0 - m) + 255.0 * m


# --------------------------------------------------------------------------
# camera
# --------------------------------------------------------------------------
@dataclass
class CameraPath:
    """Camera keys in normalised source coordinates.

    Each key is ``(t, cx, cy, zoom)``; ``zoom`` 1.0 shows the whole plate.
    Values ease in and out between keys, so a two-key path is a slow push or
    drift rather than a linear slide.
    """

    keys: tuple[tuple[float, float, float, float], ...]
    handheld: float = 0.4
    seed: int = 0

    def at(self, t: float) -> tuple[float, float, float]:
        keys = self.keys
        if t <= keys[0][0]:
            return keys[0][1], keys[0][2], keys[0][3]
        for k0, k1 in zip(keys, keys[1:]):
            if t <= k1[0]:
                span = max(k1[0] - k0[0], 1e-6)
                f = ease_in_out((t - k0[0]) / span)
                return (lerp(k0[1], k1[1], f), lerp(k0[2], k1[2], f), lerp(k0[3], k1[3], f))
        return keys[-1][1], keys[-1][2], keys[-1][3]

    def jitter(self, t: float) -> tuple[float, float]:
        """Sub-pixel operator breathe: sums of incommensurate sines, no RNG."""
        if self.handheld <= 0.0:
            return 0.0, 0.0
        a = self.handheld
        dx = a * (0.55 * np.sin(t * 0.83 + self.seed) + 0.30 * np.sin(t * 2.31 + self.seed * 2))
        dy = a * (0.55 * np.sin(t * 0.71 + self.seed * 3) + 0.30 * np.sin(t * 2.07 + self.seed * 5))
        return float(dx), float(dy)


def _crop_at(cx: float, cy: float, zoom: float, src_w: int, src_h: int,
             width: int, height: int):
    aspect_out = width / height
    aspect_src = src_w / src_h
    if aspect_src >= aspect_out:
        base_h, base_w = float(src_h), src_h * aspect_out
    else:
        base_w, base_h = float(src_w), src_w / aspect_out
    half_w, half_h = base_w / (2.0 * zoom), base_h / (2.0 * zoom)
    cx = float(np.clip(cx * src_w, half_w, src_w - half_w))
    cy = float(np.clip(cy * src_h, half_h, src_h - half_h))
    return cx, cy, half_w, half_h


def camera_maps(width: int, height: int, src_w: int, src_h: int,
                cx: float, cy: float, zoom: float,
                shift: tuple[float, float] = (0.0, 0.0),
                scale_mul: float = 1.0):
    """Sampling maps for an output frame; the crop can never leave the plate."""
    cx, cy, half_w, half_h = _crop_at(cx, cy, zoom, src_w, src_h, width, height)
    half_w /= scale_mul
    half_h /= scale_mul
    xs = (np.arange(width, dtype=np.float32) / (width - 1) - 0.5) * (2 * half_w) + cx + shift[0]
    ys = (np.arange(height, dtype=np.float32) / (height - 1) - 0.5) * (2 * half_h) + cy + shift[1]
    return (np.broadcast_to(xs[None, :], (height, width)).astype(np.float32),
            np.broadcast_to(ys[:, None], (height, width)).astype(np.float32))


# --------------------------------------------------------------------------
# the still itself
# --------------------------------------------------------------------------
@dataclass
class LivingStill:
    """A photographed scene with depth-layered parallax and atmosphere.

    Parameters
    ----------
    rgb            approved still, uint8 RGB
    path           camera keys (t, cx, cy, zoom)
    parallax       near-layer travel in source pixels at the end of the shot
    focus_pull     how far the far layer drifts out of focus over the shot
    horizon        where the depth ramp pivots (0 top .. 1 bottom)
    snow           optional atmospheric field
    breath         slow exposure/luminance breathing amplitude
    """

    rgb: np.ndarray
    path: CameraPath
    parallax: float = 4.0
    focus_pull: float = 0.35
    horizon: float = 0.55
    snow: SnowField | None = None
    breath: float = 0.02
    seed: int = 0
    depth_mode: bool = True
    _depth: np.ndarray | None = field(default=None, repr=False)
    _far: np.ndarray | None = field(default=None, repr=False)

    def prepare(self) -> "LivingStill":
        if self.depth_mode and self._depth is None:
            self._depth = depth_proxy(self.rgb, horizon=self.horizon)
        return self

    def render(self, t: float, width: int, height: int) -> np.ndarray:
        """One frame at ``t``. One warp, one defocus, no double exposure.

        The camera and the parallax are combined into a *single* displacement
        map: the base crop plus a per-pixel shift scaled by the depth proxy. A
        near pixel travels further than a far pixel, so the room has real
        parallax -- but every output pixel is sampled from exactly one place in
        the plate, which is what keeps the frame sharp. Blending two warps of
        the same plate (the obvious first approach) ghosts on anything that
        spans the depth gradient: a person's head against the window tears into
        horizontal streaks. That cannot happen here.

        Defocus is the same trick: the far part of the *already warped* frame is
        softened, so the two versions share one geometry and can be blended
        safely.
        """
        src_h, src_w = self.rgb.shape[:2]
        cx, cy, zoom = self.path.at(t)
        jx, jy = self.path.jitter(t)
        map_x, map_y = camera_maps(width, height, src_w, src_h, cx, cy, zoom, (jx, jy))

        t0, t1 = self.path.keys[0][0], self.path.keys[-1][0]
        p = float(np.clip((t - t0) / max(t1 - t0, 1e-6), 0.0, 1.0))
        travel = self.parallax * ease_in_out(p)

        if not self.depth_mode or self._depth is None:
            out = cv2.remap(self.rgb, map_x, map_y, cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_REFLECT_101)
        else:
            depth = cv2.remap(self._depth, map_x, map_y, cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REFLECT_101)
            dx = (travel * (depth - 0.45)).astype(np.float32)
            dy = (travel * 0.22 * (depth - 0.45)).astype(np.float32)
            out = cv2.remap(self.rgb, map_x + dx, map_y + dy, cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_REFLECT_101)
            if self.focus_pull > 0.0:
                # far content loses definition as the shot develops; the blend
                # weight is the same depth map, so the two images are aligned
                amount = float(np.clip(self.focus_pull * p, 0.0, 1.0)) * 1.6
                if amount > 0.02:
                    soft = cv2.GaussianBlur(out, (0, 0), amount)
                    w_far = np.clip(1.0 - depth * 2.0, 0.0, 1.0)[..., None]
                    out = (out.astype(np.float32) * (1.0 - w_far)
                           + soft.astype(np.float32) * w_far)
                    out = np.clip(out, 0, 255).astype(np.uint8)

        return out

    def atmosphere(self, img: np.ndarray, t: float) -> np.ndarray:
        """Snow and exposure breath, applied *after* interpolation.

        Both are time-varying by nature. Baking them into the key images makes
        consecutive keys differ by much more than the camera move -- snow alone
        travels tens of pixels in a quarter of a second -- and the flow
        interpolator would smear that difference across the whole frame. Doing
        it here also means the snow moves at the full 24 fps.
        """
        out = img.astype(np.float32)
        if self.breath > 0.0:
            out *= 1.0 + self.breath * float(np.sin(2 * np.pi * t / 7.3 + self.seed))
        if self.snow is not None:
            out = self.snow.apply(out, t)
        return np.clip(out, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------
# geometry helpers for footage
# --------------------------------------------------------------------------
def fit_cover(frame: np.ndarray, width: int, height: int,
              sharpen: float = 0.18) -> np.ndarray:
    """Centre-crop to the delivery aspect, then scale -- never stretch.

    The generated clips are 1280x704 .. 1344x768, so this is a real upscale.
    A small unsharp pass afterwards keeps their perceived detail level close to
    the 1080p output, without inventing texture.
    """
    h, w = frame.shape[:2]
    target = width / height
    if w / h > target:
        new_w = int(round(h * target))
        x0 = (w - new_w) // 2
        frame = frame[:, x0:x0 + new_w]
    elif w / h < target:
        new_h = int(round(w / target))
        y0 = (h - new_h) // 2
        frame = frame[y0:y0 + new_h, :]
    if frame.shape[1] != width or frame.shape[0] != height:
        # Lanczos for the one big step from clip resolution to delivery size:
        # these are 1280x704 sources going to 1920x1080, so the scaler is the
        # single biggest influence on how crisp the footage looks
        frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LANCZOS4)
    if sharpen > 0.0:
        blur = cv2.GaussianBlur(frame, (0, 0), 1.1)
        frame = cv2.addWeighted(frame, 1.0 + sharpen, blur, -sharpen, 0.0)
    return frame
