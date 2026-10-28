"""Subject matte extraction for layered 2.5D compositing.

Every keyframe shares one high-key overcast plate: pale snow, pale sky, a
distant ridge and a band of conifers. The skier and all of his kit are far
darker than that plate, and most of the kit is physically connected to him
(gloves grip the poles, boots sit on the skis). The subject is therefore one
large connected dark region; other dark regions are scenery (trees, ridge
rock) or detached kit (a thrown pole, a released ski), which the caller can
name explicitly with include/exclude seed points.

The output is a soft-edged float matte used only as a compositing mask. It
makes no claim about the provenance of the source images.
"""

from __future__ import annotations

import cv2
import numpy as np


def _dark_mask(gray: np.ndarray, thresh: float) -> np.ndarray:
    d = (gray < thresh).astype(np.uint8)
    d = cv2.morphologyEx(d, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    d = cv2.morphologyEx(d, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return d


def subject_matte(rgb: np.ndarray, thresh: float = 132.0, grow_px: int = 2,
                  include=(), exclude=(), feather: float = 1.5):
    """Soft matte for the skier plus his visibly attached/detached equipment.

    ``include`` / ``exclude`` are sequences of normalised (x, y) points naming
    dark components that must be added or removed.
    """
    h, w = rgb.shape[:2]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    d = _dark_mask(gray, thresh)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(d, 8)

    best, best_score = None, -1.0
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < 1500:
            continue
        cx, cy = cent[i]
        score = area * (1.0 - 0.6 * (abs(cx - w / 2) / w + abs(cy - h * 0.55) / h))
        if score > best_score:
            best, best_score = i, score
    if best is None:
        raise RuntimeError("subject seed not found")

    def warm(i):
        """Distant conifers/rock read warm (R > B); the navy kit reads cool."""
        comp = lab == i
        px = rgb[comp].astype(np.float32)
        return float(px[:, 0].mean() - px[:, 2].mean())

    keep = {int(best)}
    # absorb fragments that all but touch the subject (pole tips, boot edges)
    gap = cv2.dilate((lab == best).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    for i in range(1, n):
        if i == best or stats[i, cv2.CC_STAT_AREA] < 60:
            continue
        if ((lab == i) & gap).sum() > 0 and warm(i) < 6.0:
            keep.add(int(i))

    def to_xy(pt):
        px, py = float(pt[0]), float(pt[1])
        if px > 1.0 or py > 1.0:      # given in pixels
            px, py = px / max(w - 1, 1), py / max(h - 1, 1)
        xi = min(max(int(round(px * (w - 1))), 0), w - 1)
        yi = min(max(int(round(py * (h - 1))), 0), h - 1)
        return xi, yi

    for pts in include:
        for pt in np.atleast_2d(pts):
            xi, yi = to_xy(pt)
            lid = int(lab[yi, xi])
            if lid > 0 and (lid == best or warm(lid) < 6.0):
                keep.add(lid)
    for pts in exclude:
        for pt in np.atleast_2d(pts):
            xi, yi = to_xy(pt)
            lid = int(lab[yi, xi])
            if lid > 0 and lid != best:
                keep.discard(lid)

    m8 = np.isin(lab, list(keep)).astype(np.uint8)
    if grow_px:
        m8 = cv2.dilate(m8, np.ones((2 * grow_px + 1,) * 2, np.uint8))

    # fill enclosed holes (face, goggles, jacket highlights are brighter than
    # the threshold but sit inside the silhouette)
    ff = m8.copy()
    mk = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(ff, mk, (0, 0), 1)
    m8 = np.maximum(m8, (ff == 0).astype(np.uint8))

    # drop anything no longer connected to the main subject blob
    nn, ll, _, _ = cv2.connectedComponentsWithStats(m8, 8)
    seed_ids = set(np.unique(ll[lab == best]).tolist()) - {0}
    for pts in include:
        for pt in np.atleast_2d(pts):
            xi, yi = to_xy(pt)
            seed_ids.add(int(ll[yi, xi]))
    keepmask = np.zeros_like(m8)
    for i in range(1, nn):
        if i in seed_ids:
            keepmask[ll == i] = 1
    keepmask = cv2.morphologyEx(keepmask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

    soft = cv2.GaussianBlur(keepmask.astype(np.float32), (0, 0), feather)
    grad = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, 3)) + np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, 3))
    edge = np.clip(grad / 120.0, 0.0, 1.0)
    crisp = cv2.GaussianBlur(keepmask.astype(np.float32), (0, 0), 0.4)
    m = edge * crisp + (1.0 - edge) * soft
    return np.clip(m, 0.0, 1.0)


def refine_with_plate(matte, frame, plate, thresh=16.0, floor=0.06):
    """Drop matte areas that look like the static plate (leaked scenery)."""
    diff = np.abs(frame.astype(np.float32) - plate.astype(np.float32)).mean(axis=2)
    diff = cv2.GaussianBlur(diff, (0, 0), 2.0)
    evidence = np.clip((diff - thresh) / 12.0, 0.0, 1.0)
    m = matte * np.maximum(evidence, floor)
    m = cv2.GaussianBlur(m, (0, 0), 1.0)
    # re-close interior holes opened by the evidence test
    hard = (m > 0.35).astype(np.uint8)
    ff = hard.copy()
    mk = np.zeros((hard.shape[0] + 2, hard.shape[1] + 2), np.uint8)
    cv2.floodFill(ff, mk, (0, 0), 1)
    filled = np.maximum(hard, (ff == 0).astype(np.uint8))
    filled = cv2.morphologyEx(filled, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    nn, ll, stats, _ = cv2.connectedComponentsWithStats(filled, 8)
    if nn > 1:
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        filled = (ll == big).astype(np.uint8)
    soft = cv2.GaussianBlur(filled.astype(np.float32), (0, 0), 1.2)
    return np.clip(np.maximum(soft, m * 0.0), 0.0, 1.0)


def plate_from_keyframes(mattes, frames, weight=None, bg_thresh=0.10):
    """Rebuild a clean background plate from the pixels the subject never covers.

    Only pixels that are convincingly background in a frame contribute to that
    frame's estimate, so a moving subject can never leak into the plate (which
    would in turn make the subject look "static" and get masked out).
    Pixels that are covered in every frame are inpainted from their surrounds.
    """
    n = len(frames)
    h, w = frames[0].shape[:2]
    stack = np.stack([f.astype(np.float32) for f in frames])
    cover = np.stack(mattes).astype(np.float32)

    if weight is None:
        weight = np.ones(n, np.float32)
    wsum = np.asarray(weight, dtype=np.float32)[:, None, None, None]

    valid = (cover < bg_thresh).astype(np.float32)[..., None]
    bg_w = valid * wsum + 1e-6
    num = (stack * bg_w).sum(axis=0)
    den = bg_w.sum(axis=0)
    plate = num / den

    covered = (valid.sum(axis=0)[..., 0] == 0)
    if covered.any():
        mask = (covered.astype(np.uint8)) * 255
        mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))
        filled = cv2.inpaint(np.clip(plate, 0, 255).astype(np.uint8), mask, 5, cv2.INPAINT_TELEA)
        plate = np.where(covered[..., None], filled.astype(np.float32), plate)
    return np.clip(plate, 0, 255)


def composite(plate: np.ndarray, subject: np.ndarray, matte: np.ndarray):
    a = matte[..., None]
    return np.clip(subject.astype(np.float32) * a + plate.astype(np.float32) * (1 - a), 0, 255)
