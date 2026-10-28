"""Continuous camera move: modest push-in plus a stabilised follow of the action."""

from __future__ import annotations

import cv2
import numpy as np


class CameraMove:
    """Renders the 2.5D camera move over an already-warped keyframe blend.

    ``focus_points`` are normalised (x, y) coordinates in [0, 1] giving where
    the action sits in each keyframe. They are interpolated with the same
    C1-continuous timeline as the picture, which keeps the camera tracking the
    fall smoothly instead of snapping. ``zoom`` grows from ``zoom_start`` to
    ``zoom_end`` across the shot (the push-in).
    """

    def __init__(self, timeline, focus_points, zoom_start=1.00, zoom_end=1.10,
                 shift=(0.0, 0.0), drift=(0.0, 0.0), duration=None):
        self.timeline = timeline
        self.duration = float(duration if duration is not None else timeline.end)
        self.focus = np.asarray(focus_points, dtype=np.float64)
        self.zoom_start = zoom_start
        self.zoom_end = zoom_end
        self.shift = np.asarray(shift, dtype=np.float64)
        self.drift = np.asarray(drift, dtype=np.float64)

    def focus_at(self, t: float) -> np.ndarray:
        u = float(np.clip(self.timeline(t), 0.0, len(self.focus) - 1.0))
        i = int(np.floor(u))
        if i >= len(self.focus) - 1:
            return self.focus[-1].copy()
        a = u - i
        return self.focus[i] * (1 - a) + self.focus[i + 1] * a

    def zoom_at(self, t: float) -> float:
        span = max(self.duration - self.timeline.start, 1e-6)
        p = float(np.clip((t - self.timeline.start) / span, 0.0, 1.0))
        # slower start, gentle acceleration: a dolly that never overshoots
        p = 0.35 * p + 0.65 * (p * p * (3 - 2 * p))
        return self.zoom_start + (self.zoom_end - self.zoom_start) * p

    def render(self, img: np.ndarray, t: float) -> np.ndarray:
        h, w = img.shape[:2]
        span = max(self.duration - self.timeline.start, 1e-6)
        p = float(np.clip((t - self.timeline.start) / span, 0.0, 1.0))
        z = self.zoom_at(t)
        fx, fy = self.focus_at(t)
        fx += self.shift[0] + self.drift[0] * p
        fy += self.shift[1] + self.drift[1] * p

        # keep the framed area inside the plate
        half_x = 0.5 / z
        half_y = 0.5 / z
        fx = float(np.clip(fx, half_x, 1.0 - half_x))
        fy = float(np.clip(fy, half_y, 1.0 - half_y))

        xs = (np.arange(w, dtype=np.float32) / max(w - 1, 1) - 0.5) / z + fx
        ys = (np.arange(h, dtype=np.float32) / max(h - 1, 1) - 0.5) / z + fy
        map_x = np.repeat((xs * (w - 1))[None, :], h, axis=0).astype(np.float32)
        map_y = np.repeat((ys * (h - 1))[:, None], w, axis=1).astype(np.float32)
        out = cv2.remap(
            img, map_x, map_y, interpolation=cv2.INTER_LANCZOS4,
            borderMode=cv2.BORDER_REFLECT_101,
        )
        return out
