"""Optical-flow retiming and interpolation.

Two jobs, one engine:

1. **Re-timing genuine footage.** The three generated clips are 24 fps and
   8-10 s long. Playing them straight gives ~26 s of picture. Re-timed with
   per-frame optical flow they become smooth 24 fps slow motion (and speed
   ramps), so the same footage carries a 40+ second film without a single
   duplicated frame.

2. **Key-image interpolation.** Still-based shots are rendered as key images at
   a fixed cadence (4 per second by default -- the "160 pictures for 40
   seconds" idea), then interpolated between with the same flow engine at the
   full 24 fps. That keeps the authored 2.5D motion while producing a new,
   genuinely different image on every frame.

Flow is computed with DIS at reduced scale and lifted back to full resolution;
the interpolator weights both warps by forward/backward consistency so
disoccluded areas do not ghost.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import cv2
import numpy as np

cv2.setNumThreads(max(1, min(4, cv2.getNumberOfCPUs())))


# --------------------------------------------------------------------------
# flow primitives
# --------------------------------------------------------------------------
def _gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if img.ndim == 3 else img


def dis_flow(src: np.ndarray, dst: np.ndarray, scale: float = 0.55) -> np.ndarray:
    """Dense forward flow src -> dst, returned at src resolution (H, W, 2)."""
    g0 = _gray(src)
    g1 = _gray(dst)
    h, w = g0.shape[:2]
    if scale != 1.0:
        size = (max(8, int(w * scale)), max(8, int(h * scale)))
        a = cv2.resize(g0, size, interpolation=cv2.INTER_AREA)
        b = cv2.resize(g1, size, interpolation=cv2.INTER_AREA)
    else:
        a, b = g0, g1
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    dis.setUseSpatialPropagation(True)
    dis.setFinestScale(1)
    flow = dis.calc(a, b, None)
    if scale != 1.0:
        flow = cv2.resize(flow, (w, h), interpolation=cv2.INTER_LINEAR) / scale
    return flow.astype(np.float32)


_GRIDS: dict[tuple[int, int], tuple[np.ndarray, np.ndarray]] = {}


def _grid(h: int, w: int) -> tuple[np.ndarray, np.ndarray]:
    """Cached coordinate grids -- they are constant per frame size."""
    key = (h, w)
    grid = _GRIDS.get(key)
    if grid is None:
        x = np.broadcast_to(np.arange(w, dtype=np.float32)[None, :], (h, w)).copy()
        y = np.broadcast_to(np.arange(h, dtype=np.float32)[:, None], (h, w)).copy()
        grid = (x, y)
        _GRIDS[key] = grid
    return grid


def warp(img: np.ndarray, flow: np.ndarray, amount: float) -> np.ndarray:
    h, w = img.shape[:2]
    gx, gy = _grid(h, w)
    return cv2.remap(
        img, gx + amount * flow[..., 0], gy + amount * flow[..., 1],
        interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE,
    )


def blend_flow(a: np.ndarray, b: np.ndarray, p: float,
               fab: np.ndarray, fba: np.ndarray,
               trust_sigma: float = 3.2) -> np.ndarray:
    """Frame at position ``p`` between ``a`` and ``b`` (uint8 RGB in, uint8 out)."""
    p = float(np.clip(p, 0.0, 1.0))
    if p <= 1e-3:
        return a
    if p >= 1.0 - 1e-3:
        return b
    h, w = a.shape[:2]
    wa = warp(a, fab, p)
    wb = warp(b, fba, 1.0 - p)

    # forward/backward consistency, evaluated at half resolution: the weight is
    # heavily smoothed anyway, and this is the most expensive step per frame
    half_w, half_h = max(2, w // 2), max(2, h // 2)
    fab_s = fab[::2, ::2]
    fba_s = fba[::2, ::2]
    gxs, gys = _grid(half_h, half_w)
    bx = np.clip(gxs + fab_s[..., 0] * 0.5, 0, half_w - 1).astype(np.int32)
    by = np.clip(gys + fab_s[..., 1] * 0.5, 0, half_h - 1).astype(np.int32)
    err = np.linalg.norm(fab_s * 0.5 + fba_s[by, bx], axis=2)
    trust = np.exp(-(err / trust_sigma) ** 2)
    weight = p * trust + (1.0 - trust) * (1.0 if p > 0.5 else 0.0)
    weight = cv2.GaussianBlur(weight.astype(np.float32), (0, 0), 0.8)
    weight = cv2.resize(weight, (w, h), interpolation=cv2.INTER_LINEAR)[..., None]
    out = wa.astype(np.float32) * weight + wb.astype(np.float32) * (1.0 - weight)
    return np.clip(out, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------
# retiming a clip
# --------------------------------------------------------------------------
@dataclass
class Speed:
    """Piecewise-linear speed profile in *source frames per output frame*.

    ``points`` are (local output seconds, speed). Below 1.0 is slow motion,
    above 1.0 is a speed ramp. Linear interpolation keeps accel continuous to
    the eye, and the integrated position is evaluated per output frame, so the
    result is deterministic and monotonic.
    """

    points: tuple[tuple[float, float], ...] = ((0.0, 1.0),)

    def at(self, t: float) -> float:
        pts = self.points
        if t <= pts[0][0]:
            return pts[0][1]
        for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
            if t <= t1:
                f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                return v0 + (v1 - v0) * f
        return pts[-1][1]

    def positions(self, count: int, fps: float, start: float) -> np.ndarray:
        """Source frame position for each output frame."""
        pos = np.empty(count, dtype=np.float64)
        acc = float(start)
        dt = 1.0 / fps
        for i in range(count):
            pos[i] = acc
            acc += self.at(i * dt) * 1.0  # one output frame step
        return pos


class ClipRetimer:
    """Pulls re-timed frames out of a :class:`~filmkit.sources.ClipReader`."""

    def __init__(self, reader, start_frame: float, seconds: float, fps: float,
                 speed: Speed, shutter: float = 0.0, validate: bool = True):
        self.reader = reader
        self.start = float(start_frame)
        self.fps = float(fps)
        self.speed = speed
        self.shutter = float(shutter)
        count = max(1, int(round(seconds * fps)))
        self.count = count
        self.positions = self.speed.positions(count, fps, self.start)
        if validate:
            last = self.positions[-1] + 1.0
            if last > reader.info.frames + 0.5:
                raise ValueError(
                    f"{reader.info.path.name}: retime needs source frame {last:.1f} "
                    f"but the clip has {reader.info.frames}"
                )
        self._pair: tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None = None

    def _pair_at(self, i0: int):
        """Frames i0/i0+1 together with both flows, cached as one unit.

        Holding the decoded frames next to their flows matters: asking the
        decoder for i0, then i0+1, then going back to i0 for the next output
        frame would force a seek on every frame of the film.
        """
        if self._pair is not None and self._pair[0] == i0:
            return self._pair[1:]
        a = self.reader.frame(i0)
        b = self.reader.frame(i0 + 1)
        fab = dis_flow(a, b)
        fba = dis_flow(b, a)
        self._pair = (i0, a, b, fab, fba)
        return self._pair[1:]

    def frame(self, index: int) -> np.ndarray:
        index = int(np.clip(index, 0, self.count - 1))
        pos = float(np.clip(self.positions[index], 0.0, self.reader.info.frames - 1.001))
        i0 = int(np.floor(pos))
        p = pos - i0
        if p < 0.02:
            return self.reader.frame(i0)
        a, b, fab, fba = self._pair_at(i0)
        if self.shutter <= 0.0:
            return blend_flow(a, b, p, fab, fba)
        # 180-degree-shutter style accumulation: three sub-positions inside the
        # frame's exposure window, averaged. Hides interpolation error and reads
        # as real camera blur in slow motion.
        acc = np.zeros(a.shape, np.float32)
        for k in (-1, 0, 1):
            q = float(np.clip(p + k * self.shutter, 0.0, 1.0))
            acc += blend_flow(a, b, q, fab, fba).astype(np.float32)
        return np.clip(acc / 3.0, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------
# interpolating an arbitrary key sequence
# --------------------------------------------------------------------------
class KeyedInterpolator:
    """Turns a sparse key-image generator into a dense, smooth image stream.

    ``render_key(i)`` returns key ``i``. ``frame(u)`` with ``u`` in
    ``[0, n_keys - 1]`` returns the interpolated image at that continuous
    position. Only the two neighbouring keys are kept in memory.
    """

    def __init__(self, render_key: Callable[[int], np.ndarray], n_keys: int):
        if n_keys < 2:
            raise ValueError("need at least two key images")
        self.render_key = render_key
        self.n_keys = int(n_keys)
        self._cache: dict[int, np.ndarray] = {}
        self._pair: tuple[int, np.ndarray, np.ndarray] | None = None

    def _key(self, i: int) -> np.ndarray:
        i = int(np.clip(i, 0, self.n_keys - 1))
        if i not in self._cache:
            self._cache[i] = self.render_key(i)
            for stale in [k for k in self._cache if abs(k - i) > 1]:
                del self._cache[stale]
        return self._cache[i]

    def _flows(self, i0: int):
        if self._pair is not None and self._pair[0] == i0:
            return self._pair[1], self._pair[2]
        a, b = self._key(i0), self._key(i0 + 1)
        fab = dis_flow(a, b)
        fba = dis_flow(b, a)
        self._pair = (i0, fab, fba)
        return fab, fba

    def frame(self, u: float) -> np.ndarray:
        u = float(np.clip(u, 0.0, self.n_keys - 1.0))
        i0 = int(np.floor(u))
        p = u - i0
        if i0 >= self.n_keys - 1:
            return self._key(self.n_keys - 1)
        if p < 0.015:
            return self._key(i0)
        fab, fba = self._flows(i0)
        return blend_flow(self._key(i0), self._key(i0 + 1), p, fab, fba)
