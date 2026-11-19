"""The 17 photographs supplied specifically for the Dubravnaya edit.

Order matches the attachment list. The earlier Spartak photographs are not part
of this manifest and are never read by the Dubravnaya renderer.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SHARED = BASE.parent
REPO = SHARED.parent

PHOTO_NAMES = (
    'IMG_6976',
    'IMG_6757',
    'IMG_6751',
    '3a003eeb6f62ae091f04215208f19bec',
    'IMG_6747',
    'IMG_6701',
    'IMG_6657',
    'IMG_6659',
    'IMG_6645',
    'IMG_6639',
    'IMG_6636',
    'IMG_6633',
    'IMG_6612',
    'IMG_6606',
    'IMG_6584',
    'IMG_6223',
    'IMG_1881',
)
