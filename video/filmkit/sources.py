"""Hash-pinned, read-only access to the approved material.

Every frame of v3 comes from exactly one of these files. The pins are checked
before a render starts, so a changed or regenerated source is a hard error
instead of a silent visual drift. Nothing in this module writes to the source
tree.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]

# --------------------------------------------------------------------------
# Pinned sources. `kind` decides how the file may be used:
#   clip  - genuine generated footage (moving image)
#   still - approved reference still, may only be moved by camera/matte work
#   vo    - approved, locked voice-over (never re-timed, re-worded or edited)
# --------------------------------------------------------------------------
PINNED: dict[str, tuple[str, str, str]] = {
    # key: (relative path, sha256, kind)
    "clip_carve": ("scene a1.mp4",
                   "1c177a724a20339a832200b41334d2388e1f268c84c3cef1eb541caae5ac2ead", "clip"),
    "clip_fall": ("scene a2.mp4",
                  "a93cec75210e159b0d569b0d8919bb47f7ebd9332ea886f4c0e0c842a785848e", "clip"),
    "clip_return": ("scene d.mp4",
                    "c77b1ddf0c3cd79508d5c5c0d02e9441f0aa6b380810a12464edf1a5ba2723bd", "clip"),

    "dawn_valley": ("video/assets/endcard_altai_landscape_v1.png",
                    "2beca354122fe5ffac84b43c1ddd27e06be63db3fa37a172fc8b28d060061e5c", "still"),
    "aftermath": ("references/scenes/REF-SCENE-02-injury-aftermath-v2.png",
                  "4b4e21eed7a5b62d368782c4c5b805f836e07fd1ac9ecba932bf3a6fd0ac5074", "still"),
    "exterior": ("references/scenes/REF-SCENE-03-center-exterior-reveal.png",
                 "3cff05af0b82055281a203e5187ac4a0266cd4f53d6b05440de280dc74543ac0", "still"),
    "reception": ("references/scenes/REF-SCENE-04-reception-welcome.png",
                  "dcc6b97af2e1452d9a09a6bf5397ab1b8282a56c08aac864cecf9db7a6f00320", "still"),
    "rehab_room": ("references/interiors/REF-INT-02-master-rehabilitation-room.png",
                   "ad355398dd775ad6f0f0f4c33968e75f8ac7281d9fafea9aab5a83b03b3ffe62", "still"),
    "assessment": ("references/scenes/REF-SCENE-05-biomechanics-assessment-v2.png",
                   "0a6d303ee25232ba9d82474e120001cbcf0c2813debdaf9ea44d3031f4722acb", "still"),
    "exercises": ("references/scenes/REF-SCENE-06-rehabilitation-exercises.png",
                  "d163d7baab6f34d2cc5720e3b68782adb7389b22a83af793c54fa442395ad9de", "still"),
    "physio": ("references/scenes/REF-SCENE-07-recovery-physiotherapy.png",
               "a3899eb7d0c1a5470c7fa90dc31e3760e3dd9dfc56e0ac519855911d542618e1", "still"),
    "team": ("references/scenes/REF-SCENE-08-rehabilitation-team.png",
             "581c44ba71f91d3de5a0f3447246e3d406afa7427b99e60d95db6a5ba15ef749", "still"),
    "return_still": ("references/scenes/REF-SCENE-09-return-to-slopes.png",
                     "5eec2e8d9dc4730241c10500e2541b97da51475827d714b1c5f5e9ccb7626897", "still"),
    "brand_plate": ("references/scenes/REF-SCENE-10-final-brand-card.png",
                    "5c173731529dd1899046b842997d798865a2059062f0a6cec99696a9afdc7486", "still"),
    "voiceover": ("audio/voiceover/voiceover_ru_full_v1.mp3",
                  "7d5368d3075ba16c30e9f6bf717d477c1ff2c6eb51bf59dba2a86b6d199376f1", "vo"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(quiet: bool = False) -> dict[str, Path]:
    """Check every pin and return key -> absolute path. Raises on any drift."""
    paths: dict[str, Path] = {}
    for key, (relative, expected, kind) in PINNED.items():
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"required {kind} source is missing: {relative}")
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"{kind} source changed: {relative}\n  expected {expected}\n  actual   {actual}\n"
                "v3 refuses to render from modified approved material."
            )
        paths[key] = path
        if not quiet:
            print(f"  ok  {kind:5s} {relative}")
    return paths


# --------------------------------------------------------------------------
# Video clips
# --------------------------------------------------------------------------
@dataclass
class ClipInfo:
    path: Path
    width: int
    height: int
    fps: float
    frames: int

    @property
    def duration(self) -> float:
        return self.frames / self.fps if self.fps else 0.0


class ClipReader:
    """Sequential reader with one cached seek target (no full decode into RAM).

    ``frame(i)`` is cheap while requests move forward, which is exactly how the
    timeline consumes it. A backwards request seeks; that is rare and explicit.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self._cap = cv2.VideoCapture(str(self.path))
        if not self._cap.isOpened():
            raise RuntimeError(f"cannot open clip {self.path}")
        fps = self._cap.get(cv2.CAP_PROP_FPS) or 24.0
        self.info = ClipInfo(
            path=self.path,
            width=int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            fps=float(fps),
            frames=int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        )
        self._pos = -1
        self._last: np.ndarray | None = None

    def frame(self, index: int) -> np.ndarray:
        """RGB uint8 frame at ``index`` (clamped)."""
        index = int(np.clip(index, 0, self.info.frames - 1))
        if index == self._pos and self._last is not None:
            return self._last
        if index <= self._pos or self._pos < 0 or index - self._pos > 12:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, index)
            self._pos = index
            ok, frame = self._cap.read()
        else:
            ok = False
            frame = None
            while self._pos < index:
                ok, frame = self._cap.read()
                self._pos += 1
        if not ok or frame is None:
            if self._last is not None:
                return self._last
            raise RuntimeError(f"decoder stopped at frame {index} of {self.path.name}")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self._last = rgb
        return rgb

    def release(self) -> None:
        self._cap.release()


class StillSource:
    """An approved still, held in memory once and never modified on disk."""

    def __init__(self, path: Path):
        self.path = Path(path)
        image = cv2.imread(str(self.path), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"cannot read still {self.path}")
        self.rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.height, self.width = self.rgb.shape[:2]


def load_stills(paths: dict[str, Path], keys: list[str] | None = None) -> dict[str, StillSource]:
    out: dict[str, StillSource] = {}
    for key in keys if keys is not None else list(paths):
        if PINNED[key][2] == "still":
            out[key] = StillSource(paths[key])
    return out
