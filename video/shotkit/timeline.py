"""C1-continuous parameter timeline over keyframe nodes."""

from __future__ import annotations

import numpy as np


class Timeline:
    """Maps wall-clock time to a keyframe index coordinate.

    ``times`` are the keyframe node times in seconds (strictly increasing).
    Evaluating the timeline returns a float ``u`` in ``[0, n-1]``; the integer
    part selects the keyframe pair and the fractional part is the local blend
    weight. A monotone (Fritsch-Carlson) cubic is used so the parameter is C1
    continuous across nodes -- no velocity discontinuity at a keyframe, which
    is what produces the tell-tale "stutter" of naive per-segment easing.
    """

    def __init__(self, times):
        self.times = np.asarray(times, dtype=np.float64)
        if self.times.ndim != 1 or self.times.size < 2:
            raise ValueError("need at least two keyframe times")
        if np.any(np.diff(self.times) <= 0):
            raise ValueError("keyframe times must be strictly increasing")
        self.values = np.arange(self.times.size, dtype=np.float64)
        self._slopes = self._pchip_slopes(self.times, self.values)

    @staticmethod
    def _pchip_slopes(x, y):
        h = np.diff(x)
        delta = np.diff(y) / h
        m = np.zeros_like(y)
        m[0] = delta[0]
        m[-1] = delta[-1]
        for k in range(1, len(y) - 1):
            if delta[k - 1] * delta[k] <= 0:
                m[k] = 0.0
            else:
                w1 = 2.0 * h[k] + h[k - 1]
                w2 = h[k] + 2.0 * h[k - 1]
                m[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])
        return m

    @property
    def start(self) -> float:
        return float(self.times[0])

    @property
    def end(self) -> float:
        return float(self.times[-1])

    def __call__(self, t: float) -> float:
        if t <= self.times[0]:
            # linear lead-in preserves the entry velocity
            return self.values[0] + self._slopes[0] * (t - self.times[0])
        if t >= self.times[-1]:
            return float(self.values[-1])
        i = int(np.searchsorted(self.times, t, side="right") - 1)
        i = min(i, len(self.times) - 2)
        h = self.times[i + 1] - self.times[i]
        s = (t - self.times[i]) / h
        h00 = 2 * s**3 - 3 * s**2 + 1
        h10 = s**3 - 2 * s**2 + s
        h01 = -2 * s**3 + 3 * s**2
        h11 = s**3 - s**2
        return (
            h00 * self.values[i]
            + h10 * h * self._slopes[i]
            + h01 * self.values[i + 1]
            + h11 * h * self._slopes[i + 1]
        )


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def ease_in_out(x, power=1.0):
    x = np.clip(x, 0.0, 1.0)
    return smoothstep(x) ** power


def lerp(a, b, w):
    return a + (b - a) * w
