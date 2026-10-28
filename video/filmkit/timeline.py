"""RETURN TO THE SLOPE — v3 picture timeline.

The locked Russian voice-over is the clock. Every cut is placed against a
spoken phrase, so the picture breathes with the narration instead of fighting
it. Sentence boundaries were recovered from the audio (pause detection fitted
to syllable counts, see ``docs`` in the project) and are reproduced below.

    film time   VO sentence                                   picture
    ----------------------------------------------------------------------
     0.00-  7.60  -                                          cold open: carve
     7.60- 12.20  «...ритм обрывается» / «после падения»      the fall, then quiet
    12.20- 16.60  «Ответ начинается не с громких обещаний»    the centre, mountains
    16.60- 21.40  «Сначала — разговор, внимание...»           reception, welcome
    21.40- 25.10  «Без спешки и сравнения...»                 rehabilitation hall
    25.10- 28.60  «Восстановление — не соревнование»          assessment
    28.60- 34.30  «Терпение, внимание к себе...»              hands-on therapy
    34.30- 40.40  «Иногда шаг вперёд, иногда пауза...»        movement work
    40.40- 47.20  «Не нужно доказывать готовность»            the team
    47.20- 62.00  «У каждого свой маршрут...»                 return to the slope
    62.00- 69.00  «...в своём темпе»                          dawn over the valley
    69.00- 78.00  (silence)                                   brand reveal

Picture provenance, per shot:

* ``carve``, ``fall``, ``return`` are the three generated clips, re-timed to
  24 fps with optical flow (slow motion and speed ramps). They are the only
  moving-image sources in the film.
* every other picture is an approved still, staged as a depth-layered camera
  move with atmosphere and a focus pull -- stills, honestly labelled, never
  passed off as footage.
* the end card is typeset in post from the owner-approved copy.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

import numpy as np

from . import look
from .look import Grade
from .motion import ClipRetimer, KeyedInterpolator, Speed
from .sources import ClipReader, StillSource, load_stills
from .staging import CameraPath, LivingStill, SnowField, fit_cover
from .typekit import build_end_card, composite_layers

FPS = 24
WIDTH, HEIGHT = 1920, 1080
def film_duration(shots: list["Shot"]) -> float:
    """Exact length of the laid-out film."""
    return float(shots[-1].end)
KEYS_PER_SECOND = 6.0     # authored key-image cadence (4/s also works; 6/s cuts flow error)
# Still keys are staged at (close to) source resolution and scaled up once at
# the end. Remapping three layers at 1920x1080 for every key costs ~3x more and
# adds no detail: the plates themselves are 1376x768.
WORK_W, WORK_H = 1366, 768
VO_OFFSET = 1.00          # the locked narration starts 1.0 s into the picture
# The narration is 69.95 s of speech from its first syllable. The brand card is
# never allowed to start while the narrator is still talking.
VO_END = VO_OFFSET + 69.95
CARD_START = VO_END + 0.25


# --------------------------------------------------------------------------
# shot specification
# --------------------------------------------------------------------------
@dataclass
class Shot:
    name: str
    start: float
    duration: float
    kind: str                      # "clip" | "still" | "card"
    source: str = ""
    # clip
    in_frame: float = 0.0
    speed: Speed | None = None
    shutter: float = 0.0
    # still
    camera: CameraPath | None = None
    parallax: float = 4.0
    focus_pull: float = 0.30
    horizon: float = 0.55
    snow: SnowField | None = None
    breath: float = 0.015
    # look
    grade: Grade = field(default_factory=Grade)
    grade_end: Grade | None = None
    # effects
    flash_at: float | None = None
    flash_len: float = 0.22
    fade_in: float = 0.0
    fade_out: float = 0.0
    _retimer: ClipRetimer | None = field(default=None, repr=False)
    _still: LivingStill | None = field(default=None, repr=False)
    _keys: KeyedInterpolator | None = field(default=None, repr=False)
    _card: tuple | None = field(default=None, repr=False)

    @property
    def end(self) -> float:
        return self.start + self.duration


# --------------------------------------------------------------------------
# grades
# --------------------------------------------------------------------------
COLD_DAWN = Grade(temperature=-0.34, exposure=0.03, contrast=0.22, saturation=1.06,
                  lift=0.010, bloom=0.10, halation=0.07, grain=1.8, vignette=0.17,
                  shadow_tint=(-0.012, 0.0, 0.028), highlight_tint=(0.014, 0.006, -0.008))
COLD_QUIET = Grade(temperature=-0.24, exposure=-0.02, contrast=0.20, saturation=0.84,
                   lift=0.026, bloom=0.07, halation=0.04, grain=1.6, vignette=0.20,
                   shadow_tint=(-0.010, 0.0, 0.022), highlight_tint=(0.008, 0.004, -0.004))
COLD_CENTER = Grade(temperature=-0.12, exposure=0.03, contrast=0.20, saturation=1.03,
                    bloom=0.09, halation=0.05, grain=1.5, vignette=0.15,
                    shadow_tint=(-0.014, 0.0, 0.026), highlight_tint=(0.016, 0.008, -0.006))
# Interiors: the plates arrive bright and evenly lit. A little less gain, more
# contrast and a deeper vignette give the room shape and make the skin tones sit
# forward instead of dissolving into the white ceiling.
WARM_ROOM = Grade(temperature=0.18, exposure=-0.01, contrast=0.30, saturation=1.04,
                  gain=0.955, lift=0.0, bloom=0.06, halation=0.035, grain=1.4, vignette=0.24,
                  shadow_tint=(-0.026, -0.004, 0.026), highlight_tint=(0.022, 0.010, -0.010))
WARM_HANDS = Grade(temperature=0.24, exposure=-0.01, contrast=0.30, saturation=1.05,
                   gain=0.955, lift=0.0, bloom=0.07, halation=0.04, grain=1.4, vignette=0.24,
                   shadow_tint=(-0.024, -0.004, 0.024), highlight_tint=(0.026, 0.012, -0.012))
GOLDEN = Grade(temperature=0.42, exposure=0.03, contrast=0.22, saturation=1.12,
               lift=0.004, bloom=0.13, halation=0.14, grain=1.7, vignette=0.16,
               shadow_tint=(-0.020, -0.006, 0.026), highlight_tint=(0.030, 0.014, -0.014))
GOLDEN_WIDE = Grade(temperature=0.56, exposure=0.02, contrast=0.27, saturation=1.10,
                    bloom=0.12, halation=0.14, grain=1.5, vignette=0.20,
                    shadow_tint=(-0.022, -0.006, 0.030), highlight_tint=(0.034, 0.016, -0.016))
CARD = Grade(temperature=0.05, exposure=0.0, contrast=0.06, saturation=0.95,
             bloom=0.04, halation=0.02, grain=1.0, vignette=0.24)


def blend_grades(a: Grade, b: Grade, p: float) -> Grade:
    if p <= 0.0:
        return a
    if p >= 1.0:
        return b
    out = {}
    for name in a.__dataclass_fields__:
        va, vb = getattr(a, name), getattr(b, name)
        if isinstance(va, tuple):
            out[name] = tuple(x + (y - x) * p for x, y in zip(va, vb))
        else:
            out[name] = va + (vb - va) * p
    return Grade(**out)


# --------------------------------------------------------------------------
# the film
# --------------------------------------------------------------------------
def _stretch_path(path: CameraPath | None, new_duration: float) -> CameraPath | None:
    """Scale a camera path so it still travels in one eased move."""
    if path is None:
        return None
    old = path.keys[-1][0]
    if old <= 0:
        return path
    k = new_duration / old
    return CameraPath(tuple((t * k, cx, cy, z) for t, cx, cy, z in path.keys),
                      handheld=path.handheld, seed=path.seed)


def build_shots(paths: dict, verify_only: bool = False) -> list[Shot]:
    """Lay the film down beat by beat.

    ``Beat.duration`` is the time the beat occupies including its incoming
    dissolve, so a 3.0 s beat with 0.3 s of dissolve advances the clock by
    2.7 s and the two pictures genuinely overlap.
    """
    stills: dict[str, StillSource] = load_stills(paths)
    beats: list[Shot] = []

    def still(name, dur, source, cam, *, parallax=5.0, pull=0.30, horizon=0.57,
              snow=None, breath=0.016, grade=WARM_ROOM, fade=0.0) -> None:
        beats.append(Shot(
            name=name, start=0.0, duration=dur, kind="still", source=source,
            camera=cam, parallax=parallax, focus_pull=pull, horizon=horizon,
            snow=snow, breath=breath, grade=grade, fade_in=fade,
        ))

    def clip(name, dur, source, in_frame, speed, *, shutter=0.08, grade=COLD_DAWN,
             grade_end=None, flash=None, flash_len=0.22, fade=0.25) -> None:
        beats.append(Shot(
            name=name, start=0.0, duration=dur, kind="clip", source=source,
            in_frame=in_frame, speed=speed, shutter=shutter, grade=grade,
            grade_end=grade_end, flash_at=flash, flash_len=flash_len, fade_in=fade,
        ))

    # ---- 1. the mountain, and the moment that ends the season ------------
    clip("carve", 7.15, "clip_carve", 6.0,
         Speed(((0.0, 0.66), (4.6, 0.60), (7.15, 0.50))),
         grade=COLD_DAWN, fade=0.0)
    # the fall plays at close to real speed -- a fall that reads as a graceful
    # dive is a lie -- and time only stretches as he settles into the snow
    clip("fall", 4.40, "clip_fall", 44.0,
         Speed(((0.0, 1.00), (1.3, 0.92), (2.6, 0.74), (4.4, 0.62))),
         grade=COLD_DAWN, grade_end=COLD_QUIET, flash=8.10, flash_len=0.14, fade=0.14)
    # hard cut on the quiet: the fall stops, the sound stops, he is lying there
    clip("aftermath", 3.60, "clip_fall", 134.0, Speed(((0.0, 0.56), (3.6, 0.50))),
         grade=COLD_QUIET, fade=0.0)

    # ---- 2. the centre ---------------------------------------------------
    still("exterior", 4.60, "exterior",
          CameraPath(((0.0, 0.500, 0.560, 1.020), (4.6, 0.516, 0.548, 1.115)),
                     handheld=0.55, seed=1.0),
          parallax=5.5, pull=0.30, horizon=0.62,
          snow=SnowField(count=64, speed=90.0, drift=24.0, size=1.8, opacity=0.40, seed=3),
          breath=0.012, grade=COLD_CENTER, fade=0.55)
    still("reception", 3.40, "reception",
          CameraPath(((0.0, 0.545, 0.560, 1.180), (3.4, 0.566, 0.548, 1.300)),
                     handheld=0.45, seed=2.0),
          parallax=6.0, pull=0.26, horizon=0.58, breath=0.018, grade=WARM_ROOM, fade=0.20)
    still("hall", 3.10, "rehab_room",
          CameraPath(((0.0, 0.548, 0.548, 1.080), (3.1, 0.522, 0.556, 1.200)),
                     handheld=0.40, seed=3.0),
          parallax=5.5, pull=0.26, horizon=0.56, breath=0.016, grade=WARM_ROOM, fade=0.20)
    still("assessment", 3.50, "assessment",
          CameraPath(((0.0, 0.520, 0.610, 1.260), (3.5, 0.542, 0.596, 1.390)),
                     handheld=0.40, seed=4.0),
          parallax=5.5, pull=0.34, horizon=0.60, breath=0.014, grade=WARM_ROOM)
    still("hands_on", 3.80, "physio",
          CameraPath(((0.0, 0.535, 0.590, 1.290), (3.8, 0.556, 0.576, 1.420)),
                     handheld=0.50, seed=5.0),
          parallax=5.5, pull=0.30, horizon=0.58, breath=0.020, grade=WARM_HANDS)
    still("movement", 3.20, "exercises",
          CameraPath(((0.0, 0.500, 0.600, 1.300), (3.2, 0.522, 0.586, 1.420)),
                     handheld=0.45, seed=6.0),
          parallax=6.0, pull=0.32, horizon=0.60, breath=0.018, grade=WARM_HANDS)
    still("effort", 3.40, "exercises",
          CameraPath(((0.0, 0.500, 0.470, 1.620), (3.4, 0.516, 0.458, 1.720)),
                     handheld=0.50, seed=16.0),
          parallax=5.0, pull=0.32, horizon=0.60, breath=0.018, grade=WARM_HANDS, fade=0.18)
    still("insert_detail", 2.20, "exercises",
          CameraPath(((0.0, 0.845, 0.520, 1.700), (2.2, 0.857, 0.508, 1.800)),
                     handheld=0.45, seed=21.0),
          parallax=2.5, pull=0.35, horizon=0.55, breath=0.010, grade=WARM_ROOM, fade=0.18)
    still("guidance", 3.00, "physio",
          CameraPath(((0.0, 0.560, 0.575, 1.400), (3.0, 0.585, 0.562, 1.520)),
                     handheld=0.45, seed=17.0),
          parallax=5.0, pull=0.28, horizon=0.58, breath=0.016, grade=WARM_HANDS)
    still("insert_window", 2.00, "rehab_room",
          CameraPath(((0.0, 0.395, 0.470, 1.480), (2.0, 0.378, 0.452, 1.570)),
                     handheld=0.40, seed=22.0),
          parallax=3.0, pull=0.20, horizon=0.44, breath=0.014, grade=WARM_ROOM, fade=0.18)
    still("team", 2.80, "team",
          CameraPath(((0.0, 0.560, 0.575, 1.230), (2.8, 0.575, 0.565, 1.340)),
                     handheld=0.40, seed=7.0),
          parallax=5.0, pull=0.26, horizon=0.56, breath=0.016, grade=WARM_ROOM, fade=0.20)

    # ---- 3. the return ---------------------------------------------------
    # the valley first -- "each has their own route" is spoken over the
    # mountain, not over the waiting room -- then the skier comes back
    still("dawn", 4.80, "dawn_valley",
          CameraPath(((0.0, 0.500, 0.660, 1.010), (2.4, 0.503, 0.600, 1.060),
                      (4.8, 0.500, 0.520, 1.130)), handheld=0.35, seed=8.0),
          parallax=3.0, pull=0.22, horizon=0.74,
          snow=SnowField(count=36, speed=66.0, drift=16.0, size=1.6, opacity=0.30, seed=9),
          breath=0.020, grade=GOLDEN_WIDE, fade=0.45)
    clip("return_a", 8.80, "clip_return", 5.0,
         Speed(((0.0, 0.58), (4.0, 0.53), (8.8, 0.47))),
         shutter=0.09, grade=GOLDEN, fade=0.26)
    # the last shot runs the clip to its own ending: the camera tilts up off the
    # skier into the mountain sky, which is what the brand card cuts from
    clip("return_b", 8.60, "clip_return", 137.0,
         Speed(((0.0, 0.52), (5.2, 0.50), (8.6, 0.44))),
         shutter=0.09, grade=GOLDEN, fade=0.28)

    # ---- 4. the brand ----------------------------------------------------
    # the brand card waits for the narration: the last still is extended (and
    # its camera keys stretched) to fill any gap, so the final line of the VO
    # always resolves over the picture, never over the logo
    running = sum(b.duration - (b.fade_in if b.kind != "card" else 0.0) for b in beats)
    gap = CARD_START - running
    if gap > 0.0:
        # extend the last *still* (the dawn valley), never a clip: a clip can
        # only be stretched as far as its source frames allow
        target = next(b for b in reversed(beats) if b.kind == "still")
        target.duration += gap
        target.camera = _stretch_path(target.camera, target.duration)

    beats.append(Shot(name="card", start=0.0, duration=7.60, kind="card", grade=CARD))

    # ---- shot matching -------------------------------------------------
    # The approved interiors were graded individually, so their plates arrive at
    # noticeably different brightness. On hard cuts inside one location that
    # reads as an error. Each interior is pulled a limited amount toward the
    # median of its group -- never more than a third of a stop, so the rooms keep
    # their own light -- which is what a colourist does before the final grade.
    interior = [b for b in beats if b.kind == "still" and not b.name.startswith("dawn")]
    if interior:
        luma = []
        for b in interior:
            plate = stills[b.source].rgb
            luma.append(float(plate.mean()))
        target = float(np.median(luma))
        for b, cur in zip(interior, luma):
            if cur <= 1.0:
                continue
            stops = float(np.clip(np.log2(target / cur), -0.42, 0.42)) * 0.65
            b.grade = replace(b.grade, exposure=b.grade.exposure + stops)

    # ---- lay them down with real overlaps -------------------------------
    clock = 0.0
    for beat in beats:
        beat.start = round(clock - (beat.fade_in if beat.kind != "card" else 0.0), 6)
        beat.start = max(0.0, beat.start)
        clock = beat.start + beat.duration
    # the clock now equals the end of the film
    if verify_only:
        return beats

    readers: dict[str, ClipReader] = {}
    for shot in beats:
        if shot.kind == "clip":
            reader = readers.get(shot.source)
            if reader is None:
                reader = ClipReader(paths[shot.source])
                readers[shot.source] = reader
            shot._retimer = ClipRetimer(reader, shot.in_frame, shot.duration, FPS,
                                        shot.speed, shutter=shot.shutter)
        elif shot.kind == "still":
            living = LivingStill(
                rgb=stills[shot.source].rgb, path=shot.camera, parallax=shot.parallax,
                focus_pull=shot.focus_pull, horizon=shot.horizon, snow=shot.snow,
                breath=shot.breath, seed=int(shot.camera.seed * 13) if shot.camera else 0,
            ).prepare()
            shot._still = living
            n_keys = max(2, int(round(shot.duration * KEYS_PER_SECOND)) + 1)

            def render_key(i: int, _living=living) -> np.ndarray:
                return _living.render(i / KEYS_PER_SECOND, WORK_W, WORK_H)

            shot._keys = KeyedInterpolator(render_key, n_keys)
        elif shot.kind == "card":
            background, layers = build_end_card(WIDTH, HEIGHT)
            shot._card = (background, layers)
    beats[0].fade_in = 0.0
    return beats


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
def _card_frame(shot: Shot, t: float) -> np.ndarray:
    background, layers = shot._card
    card_t = t - shot.start
    return composite_layers(background, layers, card_t)


def render_frame(shots: list[Shot], t: float) -> np.ndarray:
    """One finished, graded frame at film time ``t``."""
    active = [s for s in shots if s.start - 1e-6 <= t < s.end - 1e-6]
    if not active:
        active = [shots[-1] if t >= shots[-1].start else shots[0]]

    if len(active) == 1:
        shot = active[0]
        raw = _render_shot(shot, t)
        grade = shot.grade
    else:
        shot_a, shot_b = active[0], active[1]
        span = shot_a.end - shot_b.start
        p = float(np.clip((t - shot_b.start) / max(span, 1e-6), 0.0, 1.0))
        p = p * p * (3 - 2 * p)
        raw = look.dissolve(_render_shot(shot_a, t), _render_shot(shot_b, t), p)
        grade = blend_grades(_grade_at(shot_a, t), _grade_at(shot_b, t), p)

    frame = look.Look(grade)(raw, t, seed=int(t * 1000) % 4096)

    # the film opens from black
    if t < 1.05:
        frame = look.dip(frame, look.BLACK, 1.0 - float(np.clip(t / 1.05, 0.0, 1.0)))

    # white impact flash -- the fall is felt, never shown
    for shot in active:
        if shot.flash_at is not None:
            dt = t - shot.flash_at
            if -0.02 <= dt <= shot.flash_len:
                p = 1.0 - abs(dt) / shot.flash_len if dt < 0 else 1.0 - dt / shot.flash_len
                amount = float(np.clip(p, 0.0, 1.0)) ** 1.9 * 0.82
                frame = look.dip(frame, look.WHITE, amount)

    # fades
    first = active[0]
    if first.fade_in > 0.0 and t < first.start + first.fade_in:
        p = float(np.clip((t - first.start) / first.fade_in, 0.0, 1.0))
        frame = look.dip(frame, look.BLACK, 1.0 - p)
    # the last picture dips to black so the card can rise out of it; the card
    # itself then fades out on the very end of the film
    card = shots[-1] if shots[-1].kind == "card" else None
    last_picture = shots[-2] if card is not None else shots[-1]
    if t > last_picture.end - 0.85 and t <= last_picture.end + 1e-6:
        p = float(np.clip((t - (last_picture.end - 0.85)) / 0.85, 0.0, 1.0))
        frame = look.dip(frame, look.BLACK, p ** 1.3)
    if card is not None and t > card.end - 1.9:
        p = float(np.clip((t - (card.end - 1.9)) / 1.9, 0.0, 1.0))
        frame = look.dip(frame, look.BLACK, p ** 1.4)
    return frame


def _grade_at(shot: Shot, t: float) -> Grade:
    if shot.grade_end is None:
        return shot.grade
    span = max(shot.end - shot.start, 1e-6)
    p = float(np.clip((t - shot.start) / span, 0.0, 1.0))
    p = p * p * (3 - 2 * p)
    return blend_grades(shot.grade, shot.grade_end, p)


def _render_shot(shot: Shot, t: float) -> np.ndarray:
    local = t - shot.start
    if shot.kind == "clip":
        index = int(round(local * FPS))
        return fit_cover(shot._retimer.frame(index), WIDTH, HEIGHT)
    if shot.kind == "still":
        u = local * KEYS_PER_SECOND
        # how far is this frame being upscaled? a tight crop magnifies the plate,
        # so it needs more micro-contrast recovery than a wide establishing move
        zoom = shot.camera.at(local)[2] if shot.camera else 1.0
        plate_h = shot._still.rgb.shape[0]
        base_h = min(plate_h, shot._still.rgb.shape[1] / (WIDTH / HEIGHT))
        upscale = max(1.0, (base_h / zoom) / WORK_H)
        sharpen = float(np.clip(0.10 + 0.16 * (upscale - 1.0), 0.10, 0.30))
        frame = fit_cover(shot._keys.frame(u), WIDTH, HEIGHT, sharpen=sharpen)
        # snow, exposure breath and anything else time-varying is composited
        # after the key interpolation, so it moves at the full frame rate
        return shot._still.atmosphere(frame, local)
    return _card_frame(shot, t)


# --------------------------------------------------------------------------
# music + design plan
# --------------------------------------------------------------------------
def music_plan(duration: float):
    """Score and sound-design plan for the finished cut (times in seconds)."""
    from .audio import MusicPlan

    def chord(start_, end_, notes, voice="warm"):
        return (start_, end_, notes, voice)

    # A minor / C major family, voiced warm and open; the low register is the
    # sub, so the pad stays in the middle where it never masks the narration.
    AM9 = [57, 60, 64, 67, 71]
    EM7 = [52, 59, 62, 67, 71]
    FM9 = [53, 57, 60, 64, 67]
    CM9 = [48, 55, 59, 62, 64]
    AM7 = [57, 60, 64, 67, 72]
    G6 = [55, 59, 62, 64, 69]

    chords = [
        chord(0.0, 7.9, AM9, "dark"),
        chord(7.9, 11.9, EM7, "air"),
        chord(11.9, 16.0, FM9),
        chord(16.0, 20.6, CM9),
        chord(20.6, 24.6, AM7),
        chord(24.6, 28.4, FM9),
        chord(28.4, 33.0, CM9),
        chord(33.0, 37.6, G6),
        chord(37.6, 42.2, AM7),
        chord(42.2, 47.6, FM9),
        chord(47.6, 52.4, CM9, "open"),
        chord(52.4, 57.4, AM7, "open"),
        chord(57.4, 62.4, G6, "open"),
        chord(62.4, 68.0, FM9, "open"),
        chord(68.0, 74.0, CM9, "air"),
        chord(74.0, duration, AM9, "air"),
    ]

    # felt-piano figure: sparse, always leaving room for the narration
    piano = [
        (1.6, 76), (3.2, 72), (5.9, 69), (7.3, 67), (9.9, 64),
        (12.6, 72), (14.7, 76), (17.4, 79), (19.8, 76),
        (21.9, 69), (23.6, 72), (25.6, 77), (27.3, 72),
        (29.3, 76), (31.1, 79), (33.4, 74), (35.3, 79),
        (37.4, 83), (39.4, 79), (41.4, 76), (43.8, 72),
        (46.0, 79), (48.3, 76), (50.4, 72), (52.8, 79),
        (54.9, 84), (57.0, 81), (59.2, 76), (61.6, 79),
        (63.6, 84), (66.0, 81), (68.4, 79), (71.0, 76),
        (73.4, 72), (76.0, 69),
    ]

    pulses = [(t, 0.50 + 0.50 * min(1.0, (t - 32.0) / 22.0))
              for t in np.arange(32.0, 62.0, 1.55)]

    gain_keys = [
        (0.0, 0.0), (1.1, 0.52), (5.2, 0.76), (7.8, 0.92),
        (8.15, 0.16), (10.2, 0.09), (11.6, 0.30), (15.4, 0.50),
        (20.6, 0.60), (28.4, 0.70), (33.0, 0.78), (42.2, 0.86),
        (47.6, 0.98), (52.4, 1.05), (57.4, 1.07), (62.4, 0.98),
        (68.0, 0.82), (72.0, 0.62), (76.0, 0.24), (duration, 0.0),
    ]

    wind_keys = [
        (0.0, 0.55), (1.4, 0.85), (6.2, 0.95), (8.0, 1.0),
        (8.2, 0.10), (11.4, 0.06), (12.2, 0.26), (16.0, 0.06),
        (20.6, 0.03), (40.0, 0.03), (44.0, 0.05), (47.8, 0.45),
        (49.6, 0.85), (55.0, 0.80), (59.0, 0.52), (62.6, 0.40),
        (68.0, 0.24), (73.0, 0.10), (duration, 0.0),
    ]

    ski_keys = [
        (0.0, 0.30), (1.2, 0.70), (4.2, 0.82), (6.6, 0.95),
        (7.55, 0.85), (7.95, 0.18), (8.2, 0.0), (47.4, 0.0),
        (48.0, 0.55), (50.5, 0.85), (55.0, 0.70), (58.5, 0.30),
        (59.6, 0.0), (duration, 0.0),
    ]

    return MusicPlan(
        duration=duration,
        chords=chords,
        piano=piano,
        pulses=pulses,
        gain_keys=gain_keys,
        wind_keys=wind_keys,
        ski_keys=ski_keys,
        impact=8.10,
        whooshes=[(14.9, 0.45), (47.9, 0.85), (57.6, 0.5), (70.6, 0.55)],
        breath=[11.2, 12.2],
        reverb_wet=0.44,
    )
