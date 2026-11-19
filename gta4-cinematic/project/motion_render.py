"""Frame-continuous, independent figure motion for both intro renderers."""
from __future__ import annotations

from pathlib import Path
from PIL import Image
from motion_art import FPS, foreground_position


def motion_spec(scene, index: int, size: tuple[int, int], frames: int):
    """Return the measurable pan/zoom path for the full single-photo shot.

    The source is a still photograph: this is 2.5D camera/cutout animation,
    not artificial facial or body movement. Every photo layer is moving from
    its first to last frame, while the background has its own separate zoom.
    """
    if frames < 2:
        raise ValueError('Need at least two frames for continuous motion')
    x, y = foreground_position(scene, size)
    return {
        'x': x, 'y': y, 'width': size[0], 'height': size[1],
        'seconds': (frames-1)/FPS,
        'dx': 160 if index % 2 else -160,
        'dy': 24 if index % 4 in (0, 1) else -24,
        'zoom_start': 1.0 if index % 2 == 0 else 1.065,
        'zoom_end': 1.065 if index % 2 == 0 else 1.0,
        'grounded': scene.grounded,
    }


def figure_filters(scene, index: int, foreground: Path, frames: int):
    with Image.open(foreground) as im:
        size = im.size
    spec = motion_spec(scene, index, size, frames)
    p = f"(t/{spec['seconds']:.9f})"
    z0, dz = spec['zoom_start'], spec['zoom_end']-spec['zoom_start']
    zoom = f"({z0:.6f}+({dz:.6f})*{p})"
    # Even dimensions avoid repeated pixel-format renegotiation. Bicubic RGBA
    # scaling preserves the alpha matte and does not interpolate facial shape.
    scale = (f"[1:v]format=rgba,scale=w='trunc(iw*{zoom}/2)*2':"
             f"h='trunc(ih*{zoom}/2)*2':eval=frame:flags=bicubic,format=rgba[figure]")
    xpos = (f"{spec['x']}-(w-{spec['width']})/2+"
            f"({spec['dx']})*({p}-0.5)")
    anchor = 1 if spec['grounded'] else .5
    ypos = (f"{spec['y']}-(h-{spec['height']})*{anchor}+"
            f"({spec['dy']})*({p}-0.5)")
    overlay = (f"[bg][figure]overlay=x='{xpos}':y='{ypos}':"
               'eval=frame:shortest=1:format=auto[composite]')
    return [scale, overlay]
