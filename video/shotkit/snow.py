"""Procedural snow: atmospheric drift plus a volumetric powder burst."""

from __future__ import annotations

import cv2
import numpy as np


def _splat(shape, xs, ys, radii, alphas, blur):
    """Accumulate soft sprites additively, then compress to a density mask.

    Additive accumulation with a saturating curve (1 - exp(-k*sum)) is what
    makes overlapping crystals read as one soft cloud instead of a swarm of
    separate dots -- the visual difference between "particles" and "powder".
    """
    h, w = shape
    acc = np.zeros((h, w), dtype=np.float32)
    for x, y, r, a in zip(xs, ys, radii, alphas):
        if a <= 0.002 or r < 0.5:
            continue
        ri = int(np.ceil(r * 2.0))
        x0, x1 = int(x) - ri, int(x) + ri + 1
        y0, y1 = int(y) - ri, int(y) + ri + 1
        if x1 <= 0 or y1 <= 0 or x0 >= w or y0 >= h:
            continue
        cx0, cx1 = max(x0, 0), min(x1, w)
        cy0, cy1 = max(y0, 0), min(y1, h)
        yy, xx = np.mgrid[cy0:cy1, cx0:cx1]
        d2 = ((xx - x) ** 2 + (yy - y) ** 2) / max(r * r, 0.25)
        acc[cy0:cy1, cx0:cx1] += np.exp(-d2 * 1.35).astype(np.float32) * a
    acc = 1.0 - np.exp(-1.9 * acc)
    if blur > 0:
        acc = cv2.GaussianBlur(acc, (0, 0), blur)
    return np.clip(acc, 0.0, 1.0)


class SnowSystem:
    """Deterministic snow field for one continuous shot.

    ``bursts`` entries: ``t0``, ``center`` (normalised), ``power``, ``count``,
    optional ``tilt`` (up-slope direction of the spray). Particle positions are
    integrated analytically from an impulse with drag, so any frame can be
    rendered independently and reproducibly.
    """

    def __init__(self, width, height, fps, duration, seed=7, drift_flakes=110,
                 bursts=(), gravity=430.0, drag=2.6, wind=(-30.0, 10.0)):
        self.w, self.h = width, height
        self.fps = fps
        self.duration = duration
        self.rng = np.random.default_rng(seed)
        self.gravity = gravity
        self.drag = drag
        self.wind = np.asarray(wind, dtype=np.float64)

        n = drift_flakes
        self.d_xy = self.rng.uniform([-0.05, -0.05], [1.05, 1.1], size=(n, 2))
        self.d_v = np.stack([
            self.rng.uniform(-0.012, 0.003, n),
            self.rng.uniform(0.006, 0.034, n),
        ], axis=1)
        self.d_ph = self.rng.uniform(0, 2 * np.pi, n)
        self.d_r = self.rng.uniform(0.8, 2.6, n) ** 1.3
        self.d_a = self.rng.uniform(0.06, 0.30, n)

        self.p = {k: [] for k in
                  ("t0", "pos0", "vel", "r0", "r1", "life", "alpha", "depth",
                   "turb_ph", "turb_f", "turb_a", "ground")}
        for b in bursts:
            self._emit(b)

    def _emit(self, b):
        rng = self.rng
        n = int(b.get("count", 400))
        center = np.asarray(b["center"], dtype=np.float64)
        power = float(b.get("power", 1.0))
        cx = center[0] * self.w
        cy = center[1] * self.h

        # a powder cloud is thrown up and outward from the surface, with the
        # bulk of it drifting down-slope and toward the lens
        ang = rng.uniform(-np.pi * 1.06, -np.pi * 0.02, n)
        spread = rng.uniform(0.05, 1.0, n) ** 0.7
        speed = (rng.uniform(50, 300, n) * power) * spread
        vel = np.stack([np.cos(ang) * speed * 1.15, np.sin(ang) * speed * 1.0], axis=1)
        pos0 = np.stack([
            cx + rng.normal(0, 0.075 * self.w, n),
            cy + rng.normal(0, 0.030 * self.h, n),
        ], axis=1)
        life = rng.uniform(0.7, 2.2, n) * (0.65 + 0.5 * power)
        r0 = rng.uniform(1.6, 5.0, n) * (0.75 + 0.35 * power)
        r1 = r0 * rng.uniform(2.2, 5.5, n)
        alpha = rng.uniform(0.10, 0.34, n) * (0.6 + 0.5 * power)
        depth = rng.uniform(0.0, 1.0, n)   # 0 = near lens, 1 = in the action

        # two populations: soft billowing puffs and fine flying crystals
        puff = rng.random(n) < 0.45
        r0 = np.where(puff, r0 * 2.1, r0 * 0.65)
        r1 = np.where(puff, r0 * rng.uniform(2.4, 5.0, n), r0 * rng.uniform(1.6, 3.0, n))
        alpha = np.where(puff, alpha * 0.55, alpha * 1.15)
        turb_ph = rng.uniform(0, 2 * np.pi, (n, 2))
        turb_f = rng.uniform(1.6, 4.2, (n, 2))
        turb_a = rng.uniform(6.0, 26.0, n) * power

        self.p["t0"].append(np.full(n, float(b["t0"])))
        self.p["pos0"].append(pos0)
        self.p["vel"].append(vel)
        self.p["r0"].append(r0)
        self.p["r1"].append(r1)
        self.p["life"].append(life)
        self.p["alpha"].append(alpha)
        self.p["depth"].append(depth)
        self.p["turb_ph"].append(turb_ph)
        self.p["turb_f"].append(turb_f)
        self.p["turb_a"].append(turb_a)
        self.p["ground"].append(np.full(n, cy + 0.030 * self.h))

    def _stacked(self):
        if not self.p["t0"]:
            return {k: np.zeros(0) for k in self.p}
        return {k: np.concatenate(v) for k, v in self.p.items()}

    def layer(self, t: float):
        """Return (near_layer, cloud_layer) float32 density masks at time t."""
        near = np.zeros((self.h, self.w), dtype=np.float32)
        cloud = np.zeros((self.h, self.w), dtype=np.float32)

        # ambient drift
        tt = t
        pos = self.d_xy + self.d_v * tt
        pos[:, 0] += 0.006 * np.sin(self.d_ph + tt * 1.7)
        pos[:, 1] += 0.004 * np.cos(self.d_ph * 1.3 + tt * 1.1)
        pos = np.mod(pos, 1.0)
        px, py = pos[:, 0] * self.w, pos[:, 1] * self.h
        rad = self.d_r * (1.0 + 0.3 * np.sin(self.d_ph + tt * 2.0))
        near = np.maximum(near, _splat((self.h, self.w), px, py, rad, self.d_a, 1.1))

        d = self._stacked()
        if d["t0"].size:
            dt = t - d["t0"]
            alive = (dt > 0) & (dt < d["life"])
            if alive.any():
                dt = dt[alive]
                v0 = d["vel"][alive]
                k = self.drag
                decay = (1.0 - np.exp(-k * dt)) / k
                pos = d["pos0"][alive] + v0 * decay[:, None]
                pos[:, 1] += 0.5 * self.gravity * dt ** 2
                pos += self.wind * dt[:, None] * 0.015
                # curl-like turbulence, so the cloud edges break up
                ph, fr, ta = d["turb_ph"][alive], d["turb_f"][alive], d["turb_a"][alive]
                pos[:, 0] += ta * np.sin(fr[:, 0] * dt + ph[:, 0])
                pos[:, 1] += ta * 0.6 * np.cos(fr[:, 1] * dt + ph[:, 1])
                # snow cannot fall through the surface: it pools and rolls
                gy = d["ground"][alive]
                over = pos[:, 1] > gy
                if over.any():
                    pos[over, 1] = gy[over] + (pos[over, 1] - gy[over]) * 0.06
                    pos[over, 0] += (pos[over, 1] - gy[over]) * 1.1
                age = dt / d["life"][alive]
                rad = d["r0"][alive] + (d["r1"][alive] - d["r0"][alive]) * np.sqrt(age)
                alpha = d["alpha"][alive] * (1.0 - age) ** 1.5
                depth = d["depth"][alive]

                # the cloud proper: everything in the action plane
                cloud = np.maximum(cloud, _splat(
                    (self.h, self.w), pos[:, 0], pos[:, 1],
                    rad * 1.5, alpha * 0.85, 2.4))

                # a handful of larger, softer flakes right past the lens
                sel = depth < 0.28
                if sel.any():
                    near = np.maximum(near, _splat(
                        (self.h, self.w), pos[sel, 0], pos[sel, 1],
                        rad[sel] * 3.0, alpha[sel] * 0.55, 3.2))

        return near, cloud
