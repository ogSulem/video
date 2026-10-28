"""Dense optical-flow warping used to bend one keyframe toward its neighbour."""

from __future__ import annotations

import cv2
import numpy as np


def _to_gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)


def dense_flow(src: np.ndarray, dst: np.ndarray, preset: int = cv2.DISOPTICAL_FLOW_PRESET_MEDIUM):
    """Dense forward flow src -> dst, at full resolution of ``src``."""
    g0 = _to_gray(src)
    g1 = _to_gray(dst)
    h, w = g0.shape
    scale = 0.5 if max(h, w) > 1100 else 1.0
    if scale != 1.0:
        g0s = cv2.resize(g0, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        g1s = cv2.resize(g1, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    else:
        g0s, g1s = g0, g1
    dis = cv2.DISOpticalFlow_create(preset)
    dis.setUseSpatialPropagation(True)
    flow = dis.calc(g0s, g1s, None).astype(np.float32)
    if scale != 1.0:
        flow = cv2.resize(flow, (w, h), interpolation=cv2.INTER_LINEAR) / scale
    return flow


def _grid(h: int, w: int):
    xs = np.arange(w, dtype=np.float32)[None, :].repeat(h, axis=0)
    ys = np.arange(h, dtype=np.float32)[:, None].repeat(w, axis=1)
    return xs, ys


def warp(img: np.ndarray, flow: np.ndarray, amount: float, mode: int = cv2.INTER_LINEAR):
    """Sample ``img`` at x + amount*flow."""
    h, w = img.shape[:2]
    xs, ys = _grid(h, w)
    map_x = xs + amount * flow[..., 0]
    map_y = ys + amount * flow[..., 1]
    return cv2.remap(
        img, map_x, map_y, interpolation=mode, borderMode=cv2.BORDER_REPLICATE
    )


def blend_keyframes(a: np.ndarray, b: np.ndarray, flow_ab, flow_ba, alpha: float,
                    trust_sigma: float = 6.0):
    """Flow-warp both ends toward the in-between and blend with occlusion weights.

    ``alpha`` is the position between ``a`` (0) and ``b`` (1). Where the two
    flow fields disagree the pixel is likely disoccluded; there a plain 50/50
    blend would double-expose the subject, so the blend falls back to whichever
    keyframe is nearer in time and the shutter pass turns the result into
    motion blur rather than a ghost.
    """
    alpha = float(np.clip(alpha, 0.0, 1.0))
    if alpha <= 1e-4:
        return a.copy()
    if alpha >= 1.0 - 1e-4:
        return b.copy()

    h, w = a.shape[:2]
    wa = warp(a, flow_ab, alpha, cv2.INTER_LINEAR)
    wb = warp(b, flow_ba, (1.0 - alpha), cv2.INTER_LINEAR)

    # forward-backward consistency: where the two flow fields disagree the
    # pixel is likely occluded, so its warp is untrustworthy.
    xs, ys = _grid(h, w)
    bx = np.clip(xs + flow_ab[..., 0], 0, w - 1).astype(np.int32)
    by = np.clip(ys + flow_ab[..., 1], 0, h - 1).astype(np.int32)
    back = flow_ba[by, bx]
    err = np.linalg.norm(flow_ab + back, axis=2)
    trust = np.exp(-(err / trust_sigma) ** 2)

    # "nearest keyframe" weight as a smooth function of alpha: switching it
    # abruptly at alpha = 0.5 would pop on exactly the middle frame of every
    # segment, which is the most visible place to pop.
    x = np.clip((alpha - 0.32) / 0.36, 0.0, 1.0)
    nearest = 1.0 - (x * x * (3.0 - 2.0 * x))
    w_a = alpha * trust + nearest * (1.0 - trust)
    w_a = np.clip(w_a, 0.0, 1.0)
    w_a = cv2.GaussianBlur(w_a.astype(np.float32), (0, 0), 1.6)
    w_a = np.clip(w_a, 0.0, 1.0)[..., None]

    out = wa.astype(np.float32) * w_a + wb.astype(np.float32) * (1.0 - w_a)

    # Near either end of the segment the warped plate is only an approximation
    # of the real keyframe. Cross-fade to the true keyframe over the last 12%
    # so consecutive segments meet exactly at the node -- otherwise the
    # approximation error shows up as a one-frame pop on every keyframe.
    ramp = 0.12
    if alpha > 1.0 - ramp:
        s = (alpha - (1.0 - ramp)) / ramp
        s = s * s * (3.0 - 2.0 * s)
        out = out * (1.0 - s) + b.astype(np.float32) * s
    elif alpha < ramp:
        s = 1.0 - alpha / ramp
        s = s * s * (3.0 - 2.0 * s)
        out = out * (1.0 - s) + a.astype(np.float32) * s
    return np.clip(out, 0, 255)


def flow_magnitude(flow: np.ndarray) -> np.ndarray:
    return np.linalg.norm(flow, axis=2)
