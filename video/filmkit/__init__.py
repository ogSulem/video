"""Film kit — the v3 assembly engine for RETURN TO THE SLOPE.

The v2 renderer could only move a still image as a flat 2D crop. This kit adds
the two things that were missing, without any external service:

* :mod:`filmkit.motion` — optical-flow retiming, so genuine generated footage
  can be re-timed into smooth cinematic 24 fps (slow motion and speed ramps)
  instead of being padded by duplicated frames;
* :mod:`filmkit.staging` — 2.5D "living stills": a plate with the subject
  matted out, parallax-buffered key images generated at a fixed cadence, and
  flow interpolation between those key images at full frame rate.

Everything is deterministic and runs offline on the pinned Python stack
(NumPy, Pillow, imageio-ffmpeg, OpenCV headless).
"""

__all__ = ["sources", "motion", "staging", "look", "typekit", "audio", "timeline"]
